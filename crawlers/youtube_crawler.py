"""
YouTube 크롤러 STT 하드웨어 최적화 버전
- Mac Silicon: pywhispercpp (CoreML + Metal GPU)
- Intel/NVIDIA: faster-whisper (CUDA/CPU 자동 감지)
- 폴백: openai-whisper (범용)
- 병렬 처리 지원 (ThreadPoolExecutor)
- 크로스 플랫폼 지원 (macOS, Linux, Windows)
"""

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import os
import math
import time
import subprocess
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
from dateutil.relativedelta import relativedelta
from .common import save_to_json, parse_korean_number
import re
import tempfile
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 시스템 체크
import platform

def is_mac_silicon():
    """Mac Silicon (Apple M1/M2/M3/M4) 여부 확인"""
    return platform.system() == 'Darwin' and 'arm' in platform.machine().lower()

# STT 관련 임포트 (하드웨어 최적화)
WHISPER_AVAILABLE = False
WHISPER_LIBRARY = None

# 1순위: Mac Silicon → pywhispercpp (CoreML + Metal GPU)
if is_mac_silicon():
    try:
        from pywhispercpp.model import Model as PyWhisperCppModel
        WHISPER_AVAILABLE = True
        WHISPER_LIBRARY = "pywhispercpp"
        print("✅ Mac Silicon 감지: pywhispercpp 사용 (GPU 가속)")
    except ImportError:
        print("⚠️ pywhispercpp 미설치, faster-whisper로 폴백")

# 2순위: faster-whisper (CUDA/CPU)
if not WHISPER_AVAILABLE:
    try:
        from faster_whisper import WhisperModel
        WHISPER_AVAILABLE = True
        WHISPER_LIBRARY = "faster-whisper"
    except ImportError:
        pass

# 3순위: openai-whisper (범용 폴백)
if not WHISPER_AVAILABLE:
    try:
        import whisper
        WHISPER_AVAILABLE = True
        WHISPER_LIBRARY = "openai-whisper"
    except ImportError:
        WHISPER_AVAILABLE = False
        WHISPER_LIBRARY = None

# yt-dlp 임포트
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False

load_dotenv()


class YouTubeAudioTranscriber:
    """
    YouTube 동영상 음성 전사 클래스

    하드웨어 자동 감지 및 최적 백엔드 선택:
    - Mac Silicon: pywhispercpp (CoreML + Metal GPU)
    - Intel/NVIDIA: faster-whisper (CUDA/CPU 자동 감지)
    - 폴백: openai-whisper (범용)
    """

    def __init__(self,
                 model_size: str = None,
                 device: str = None,
                 model_path: str = None,
                 compute_type: str = "int8"):
        """
        초기화

        Args:
            model_size: Whisper 모델 크기 (tiny/base/small/medium/large)
            device: 실행 디바이스 (cpu/cuda, None이면 자동 감지)
            model_path: 모델 캐시 경로 (환경변수로 설정 가능)
            compute_type: 연산 타입 (int8/float16/float32)
        """
        # 환경변수에서 설정 읽기
        self.model_size = model_size or os.getenv("WHISPER_MODEL_SIZE", "small")
        self.model_path = model_path or os.getenv("WHISPER_MODEL_PATH", None)
        self.compute_type = compute_type

        # 디바이스 자동 감지 (NVIDIA GPU 우선)
        if device is None:
            device = os.getenv("WHISPER_DEVICE")
            if device is None and WHISPER_LIBRARY == "faster-whisper":
                try:
                    import torch
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                    if device == "cuda":
                        print("✅ NVIDIA GPU 감지: CUDA 사용")
                except ImportError:
                    device = "cpu"

        self.device = device or "cpu"

        self.model = None
        self.enabled = WHISPER_AVAILABLE and YTDLP_AVAILABLE
        # 스레드 안전성: pywhispercpp 모델은 thread-safe하지 않음
        # 병렬 처리 시 전사 작업 직렬화를 위한 락
        self._transcribe_lock = threading.Lock()

        if not self.enabled:
            missing = []
            if not WHISPER_AVAILABLE:
                missing.append("faster-whisper or openai-whisper")
            if not YTDLP_AVAILABLE:
                missing.append("yt-dlp")
            print(f"⚠️ STT 비활성화: {', '.join(missing)} 설치 필요")
            print(f"   설치: pip install faster-whisper yt-dlp ffmpeg-python")
            return

        print(f"✅ STT 사용 가능: {WHISPER_LIBRARY}")
        self._load_model()

    def _load_model(self):
        """Whisper 모델 로드"""
        if not self.enabled:
            return

        try:
            print(f"🚀 Whisper 모델 '{self.model_size}' 로드 중...")
            print(f"   라이브러리: {WHISPER_LIBRARY}")

            if WHISPER_LIBRARY == "pywhispercpp":
                # pywhispercpp 사용 (Mac Silicon GPU - Metal 자동 활성화)
                # n_threads=8: 병렬 처리 시 Progress 0% 멈춤 방지
                print("🍎 pywhispercpp 모델 로드 (Metal GPU + n_threads=8)")
                self.model = PyWhisperCppModel(self.model_size, n_threads=8)
                print(f"✅ pywhispercpp 모델 로드 완료")

            elif WHISPER_LIBRARY == "faster-whisper":
                # faster-whisper 사용
                print(f"   디바이스: {self.device}")
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    download_root=self.model_path
                )
                print(f"✅ faster-whisper 모델 로드 완료")

            else:
                # openai-whisper 사용
                print(f"   디바이스: {self.device}")
                import whisper
                self.model = whisper.load_model(
                    self.model_size,
                    device=self.device,
                    download_root=self.model_path
                )
                print(f"✅ openai-whisper 모델 로드 완료")

        except Exception as e:
            print(f"❌ Whisper 모델 로드 실패: {e}")
            self.model = None
            self.enabled = False

    def transcribe_video(self, video_url: str, video_id: str = None) -> dict:
        """
        YouTube 동영상 음성 전사

        Args:
            video_url: YouTube 동영상 URL
            video_id: 동영상 ID (로그용)

        Returns:
            {
                'success': bool,
                'text': str,
                'error': str or None,
                'duration': float (초)
            }
        """
        result = {
            'success': False,
            'text': '',
            'error': None,
            'duration': 0.0
        }

        if not self.enabled or not self.model:
            result['error'] = "STT 비활성화"
            return result

        start_time = time.time()
        temp_dir = None

        try:
            # 1. 임시 디렉토리 생성
            temp_dir = tempfile.mkdtemp(prefix="youtube_stt_")

            # 2. 오디오 다운로드
            video_info = f"[{video_id}]" if video_id else ""
            print(f"🎵 {video_info} 오디오 다운로드 중...")
            audio_path = self._download_audio(video_url, temp_dir)

            if not audio_path:
                result['error'] = "오디오 다운로드 실패"
                return result

            # 3. 음성 전사
            print(f"🎤 {video_info} 음성 전사 중...")
            transcribed_text = self._transcribe_audio(audio_path)

            if not transcribed_text:
                result['error'] = "전사 실패"
                return result

            # 4. 성공
            result['success'] = True
            result['text'] = transcribed_text
            result['duration'] = time.time() - start_time

            print(f"✅ {video_info} 전사 완료 (길이: {len(transcribed_text)}자, 소요시간: {result['duration']:.1f}초)")

        except Exception as e:
            result['error'] = str(e)
            print(f"❌ 전사 중 오류: {e}")

        finally:
            # 5. 임시 파일 정리
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"⚠️ 임시 파일 삭제 실패: {e}")

        return result

    def _download_audio(self, video_url: str, output_dir: str) -> str:
        """
        yt-dlp로 오디오 다운로드

        Args:
            video_url: YouTube 동영상 URL
            output_dir: 출력 디렉토리

        Returns:
            다운로드된 오디오 파일 경로 (실패 시 None)
        """
        try:
            output_template = os.path.join(output_dir, '%(id)s.%(ext)s')

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',  # Whisper는 WAV 선호
                    'preferredquality': '192',
                }],
                'postprocessor_args': [
                    '-ar', '16000',  # 16kHz 샘플레이트 (pywhispercpp 최적화)
                    '-ac', '1',      # 모노 채널 (STT 최적화)
                ],
                'quiet': True,
                'no_warnings': True,
                'extract_audio': True,
                # 다운로드 타임아웃 설정 (네트워크 문제 대응)
                'socket_timeout': 30,  # 소켓 타임아웃 30초
                'retries': 3,  # 재시도 3회
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                video_id = info.get('id', 'audio')

                # 다운로드된 파일 경로 찾기
                audio_path = os.path.join(output_dir, f"{video_id}.wav")

                if not os.path.exists(audio_path):
                    # .wav가 없으면 다른 확장자 찾기
                    for ext in ['mp3', 'm4a', 'opus', 'webm']:
                        alt_path = os.path.join(output_dir, f"{video_id}.{ext}")
                        if os.path.exists(alt_path):
                            audio_path = alt_path
                            break

                if os.path.exists(audio_path):
                    return audio_path
                else:
                    print(f"❌ 오디오 파일을 찾을 수 없음: {output_dir}")
                    return None

        except Exception as e:
            print(f"❌ 오디오 다운로드 실패: {e}")
            return None

    def _transcribe_audio(self, audio_path: str, stall_timeout: int = 120) -> str:
        """
        Whisper로 오디오 전사 (진행 정체 감지 포함)

        Args:
            audio_path: 오디오 파일 경로
            stall_timeout: 진행률 변화 없을 때 타임아웃 (초, 기본 120초)

        Returns:
            전사된 텍스트 (실패 시 빈 문자열)
        """
        import threading
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

        result_text = ""
        last_activity = [time.time()]  # 마지막 활동 시간 (mutable for closure)

        def run_transcription():
            nonlocal result_text
            # 스레드 안전성: 모델 접근 직렬화 (pywhispercpp는 thread-safe하지 않음)
            # 병렬 처리 시 GGML 버퍼 충돌 방지
            with self._transcribe_lock:
                try:
                    if WHISPER_LIBRARY == "pywhispercpp":
                        # pywhispercpp 사용 (Mac Silicon GPU)
                        # language="ko" = 한국어 지정 (자동감지는 노르웨이어로 오인식 발생)
                        # translate=False = 원본 언어 유지 (영어 번역 방지)
                        # no_speech_thold=0.5 = 음성 없음 임계값 낮춤 (Progress 0% 멈춤 방지)
                        segments = self.model.transcribe(
                            audio_path,
                            language="ko",
                            translate=False,
                            no_speech_thold=0.5
                        )
                        text_segments = [seg.text for seg in segments]
                        result_text = " ".join(text_segments).strip()

                    elif WHISPER_LIBRARY == "faster-whisper":
                        # faster-whisper 사용
                        segments, info = self.model.transcribe(
                            audio_path,
                            language="ko",
                            beam_size=5,
                            vad_filter=True,
                        )
                        text_segments = [segment.text for segment in segments]
                        result_text = " ".join(text_segments).strip()

                    else:
                        # openai-whisper 사용
                        result = self.model.transcribe(
                            audio_path,
                            language="ko",
                            fp16=False
                        )
                        result_text = result['text'].strip()

                except Exception as e:
                    print(f"❌ 음성 전사 실패: {e}")
                    result_text = ""

        try:
            # 별도 스레드에서 전사 실행
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_transcription)

                # 전사 완료까지 대기 (진행 중이면 계속 대기)
                # pywhispercpp는 Progress 출력하므로 stdout 활동으로 감지 가능
                # 여기서는 단순히 완료까지 대기 (전사는 자체적으로 진행됨)
                future.result()  # 완료까지 대기 (타임아웃 없음)

            return result_text

        except Exception as e:
            print(f"❌ 전사 스레드 오류: {e}")
            return ""


class YoutubeCrawler:
    """
    YouTube 크롤러 (STT 통합 버전)
    """

    def __init__(self, enable_stt: bool = None, max_workers: int = None, save_callback=None):
        """
        초기화

        Args:
            enable_stt: STT 활성화 여부 (None이면 환경변수 사용)
            max_workers: 병렬 처리 워커 수 (None이면 환경변수 사용, 기본값 3)
            save_callback: 개별 영상 수집 완료 시 호출할 콜백 함수
                          signature: (post_dict, comments_list) -> int (저장 건수)
        """
        # 실시간 저장 콜백
        self.save_callback = save_callback
        # API 키 설정
        api_keys_env = os.getenv("YOUTUBE_API_KEYS")
        print(f"🔑 YouTube API 키 환경변수: {'설정됨' if api_keys_env else '설정 안됨'}")

        if not api_keys_env:
            print("❌ YOUTUBE_API_KEYS 환경변수가 설정되지 않았습니다!")
            raise ValueError("YOUTUBE_API_KEYS 환경변수를 설정해주세요.")

        self.api_keys = api_keys_env.split(",")
        print(f"🔑 사용 가능한 API 키 개수: {len(self.api_keys)}")

        self.current_api_key_index = 0
        self.total_api_keys = len(self.api_keys)
        self.api_key = self.api_keys[0]
        self.build = build('youtube', 'v3', developerKey=self.api_key)

        self.driver = None
        self.wait = None
        self._init_browser()

        # STT 설정
        if enable_stt is None:
            enable_stt = os.getenv("YOUTUBE_STT_ENABLED", "true").lower() == "true"

        self.stt_enabled = enable_stt
        self.transcriber = None

        if self.stt_enabled:
            print("🎤 STT 기능 활성화 중...")
            self.transcriber = YouTubeAudioTranscriber()
            if not self.transcriber.enabled:
                print("⚠️ STT 초기화 실패, 비활성화됨")
                self.stt_enabled = False
        else:
            print("ℹ️ STT 기능 비활성화")

        # 병렬 처리 설정
        if max_workers is None:
            max_workers = int(os.getenv("YOUTUBE_MAX_WORKERS", "3"))
        self.max_workers = max_workers
        print(f"🔧 병렬 처리 워커 수: {self.max_workers}")

        # 브라우저 생성 동기화를 위한 락 (ChromeOptions 충돌 방지)
        import threading
        self._browser_lock = threading.Lock()

    def _get_current_api_key(self):
        """현재 사용 중인 API 키 반환"""
        return self.api_key

    def _create_browser(self):
        """
        독립적인 브라우저 인스턴스 생성 (병렬 처리용)
        락을 사용하여 ChromeOptions 동시 생성 충돌 방지

        Returns:
            (driver, wait) 튜플
        """
        # 브라우저 생성은 순차적으로 (ChromeOptions 내부 상태 충돌 방지)
        with self._browser_lock:
            try:
                options = uc.ChromeOptions()
                options.add_argument("--headless=new")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=800,600")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                options.add_experimental_option(
                    "prefs", {
                        "profile.managed_default_content_settings.images": 2,
                        "profile.managed_default_content_settings.media_stream": 2,
                        "profile.default_content_setting_values.automatic_downloads": 2,
                        "profile.default_content_setting_values.media_autoplay": 1
                    }
                )
                options.add_argument("--autoplay-policy=user-gesture-required")
                options.add_argument("--mute-audio")

                try:
                    chrome_version_output = subprocess.check_output([
                        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                        '--version'
                    ]).decode().strip()
                    chrome_version = chrome_version_output.split()[-1].split('.')[0]
                    driver = uc.Chrome(version_main=int(chrome_version), use_subprocess=True, options=options)
                except Exception:
                    driver = uc.Chrome(use_subprocess=True, options=options)

                wait = WebDriverWait(driver, 15)
                return driver, wait
            except Exception as e:
                print(f"❌ 브라우저 생성 실패: {str(e)}")
                raise

    def _init_browser(self):
        """브라우저 초기화"""
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            print("🌐 Selenium 브라우저 초기화 중...")

            # 매번 새로운 ChromeOptions 객체 생성
            options = uc.ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=800,600")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            options.add_experimental_option(
                "prefs", {
                    "profile.managed_default_content_settings.images": 2,
                    "profile.managed_default_content_settings.media_stream": 2,
                    "profile.default_content_setting_values.automatic_downloads": 2,
                    "profile.default_content_setting_values.media_autoplay": 1
                }
            )
            options.add_argument("--autoplay-policy=user-gesture-required")
            options.add_argument("--mute-audio")

            # Chrome 버전 자동 감지 (macOS)
            try:
                chrome_version_output = subprocess.check_output([
                    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                    '--version'
                ]).decode().strip()
                chrome_version = chrome_version_output.split()[-1].split('.')[0]
                print(f"🔍 감지된 Chrome 버전: {chrome_version}")
                self.driver = uc.Chrome(version_main=int(chrome_version), use_subprocess=True, options=options)
            except Exception as version_error:
                print(f"⚠️ Chrome 버전 감지 실패, 기본 드라이버 사용: {version_error}")
                self.driver = uc.Chrome(use_subprocess=True, options=options)

            self.wait = WebDriverWait(self.driver, 15)
            print("✅ Selenium 브라우저 초기화 완료")
        except Exception as e:
            print(f"❌ 브라우저 초기화 실패: {str(e)}")
            raise

    def _check_browser(self):
        """브라우저 상태 확인 및 필요 시 재시작"""
        try:
            self.driver.current_url
            return True
        except:
            print("⚠️ 브라우저가 닫혀있음. 재시작 중...")
            self._init_browser()
            return True

    def search_videos(self, keyword, start_date, end_date, max_posts):
        """YouTube API로 동영상 검색"""
        print(f"🔍 YouTube API 검색 시작: 키워드='{keyword}', 기간={start_date}~{end_date}, 최대={max_posts}")

        videos = []
        api_results_count = 50
        next_page_token = None
        fetched = 0

        # Convert start_date and end_date to ISO 8601 format
        published_after = f"{start_date}T00:00:00Z" if start_date else None
        published_before = f"{end_date}T23:59:59Z" if end_date else None

        print(f"🗓️ API 쿼리 기간: {published_after} ~ {published_before}")

        while True:
            try:
                params = {
                    'part': 'snippet',
                    'q': keyword,
                    'maxResults': api_results_count,
                    'type': 'video',
                    'key': self.api_key
                }
                if next_page_token:
                    params['pageToken'] = next_page_token
                if published_after:
                    params['publishedAfter'] = published_after
                if published_before:
                    params['publishedBefore'] = published_before

                response = self.build.search().list(**params).execute()
                items = response.get('items', [])
                print(f"📊 API 응답: {len(items)}개 동영상 발견 (전체: {fetched + len(items)}/{response.get('pageInfo', {}).get('totalResults', '?')})")

                videos.extend(items)
                fetched += len(items)

                if max_posts and fetched >= max_posts:
                    return videos[:max_posts]

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

                time.sleep(50)  # API 할당량 고려

            except KeyError:
                break
            except HttpError as e:
                if e.resp.status == 403:
                    error_reason = e.error_details[0]['reason'] if e.error_details else None
                    if error_reason == 'quotaExceeded':
                        self.current_api_key_index += 1
                        if self.current_api_key_index >= self.total_api_keys:
                            break
                        self.api_key = self.api_keys[self.current_api_key_index]
                        self.build = build('youtube', 'v3', developerKey=self.api_key)
                    else:
                        print(f"HTTP Error 403 occurred: {e}")
                        break

        return videos

    def infinite_scroll(self, driver=None):
        """댓글 무한 스크롤"""
        drv = driver or self.driver
        last_height = drv.execute_script("return document.documentElement.scrollHeight")
        prev = 0

        while True:
            drv.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(1.5)
            comment_containers = drv.find_elements(By.CSS_SELECTOR, "#comment-container")
            new = len(comment_containers)
            new_height = drv.execute_script("return document.documentElement.scrollHeight")
            if new == prev or new_height == last_height:
                break
            time.sleep(1.5)
            prev = new
            last_height = new_height

    def click_reply_button(self, comment_container, driver=None):
        """답글 버튼 클릭"""
        drv = driver or self.driver
        parent = comment_container.parent
        buttons = parent.find_elements(By.CSS_SELECTOR, "button.yt-spec-button-shape-next--call-to-action[aria-label^='답글']")

        if len(buttons) > 0:
            button = buttons[0]
            drv.execute_script("arguments[0].scrollIntoView(true);", button)
            drv.execute_script("arguments[0].click();", button)

    def convert_youtube_time(self, relative_time_str):
        """유튜브 상대 시간 변환"""
        now = datetime.now()
        target_time = None

        match = re.search(r'(\d+)\s*(분|시간|일|주|개월|년)\s*전', relative_time_str)

        if "방금 전" in relative_time_str or "오늘" in relative_time_str:
            target_time = now
        elif "어제" in relative_time_str:
            target_time = now - relativedelta(days=1)
        elif match:
            num = int(match.group(1))
            unit = match.group(2)

            if unit == '분':
                target_time = now - relativedelta(minutes=num)
            elif unit == '시간':
                target_time = now - relativedelta(hours=num)
            elif unit == '일':
                target_time = now - relativedelta(days=num)
            elif unit == '주':
                target_time = now - relativedelta(weeks=num)
            elif unit == '개월':
                target_time = now - relativedelta(months=num)
            elif unit == '년':
                target_time = now - relativedelta(years=num)

        if target_time:
            return target_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            try:
                dt_object = datetime.strptime(relative_time_str.replace('.', '').strip(), '%Y %m %d')
                return dt_object.strftime("%Y-%m-%d 00:00:00")
            except ValueError:
                return None

    def get_comments(self, video_id, driver=None):
        """댓글 수집"""
        drv = driver or self.driver
        comments = []
        comment_ids = []

        self.infinite_scroll(driver=drv)

        comment_containers = drv.find_elements(By.CSS_SELECTOR, "#comment-container")

        for i, comment_container in enumerate(comment_containers):
            comment_id = f"{video_id}_{i}"
            username = comment_container.find_element(By.CSS_SELECTOR, "#header-author").text
            username = username.split('\n')[0] if username else username
            username = username.lstrip('@') if username else username
            content = comment_container.find_element(By.CSS_SELECTOR, "#content-text").text
            like_count_text = comment_container.find_element(By.CSS_SELECTOR, "#vote-count-middle").text
            like_count = parse_korean_number(like_count_text)  # 한글 숫자 변환
            published_date = comment_container.find_element(By.CSS_SELECTOR, "#published-time-text").text
            published_date = self.convert_youtube_time(published_date)

            comments.append({
                "id": comment_id,
                "username": username,
                "content": content,
                "blog_id": video_id,
                "platform": "Youtube",
                "parent_id": None,
                "published_date": published_date,
                "like_count": like_count,
                "star_count": None,
            })
            replies = self.get_replies(comment_container, comment_id, video_id, driver=drv)
            comments.extend(replies)

        return comments

    def get_replies(self, comment_container, parent_id, blog_id, driver=None):
        """답글 수집"""
        drv = driver or self.driver
        replies = []
        self.click_reply_button(comment_container, driver=drv)

        parent = comment_container.parent
        comment_containers = parent.find_elements(By.CSS_SELECTOR, "ytd-comment-view-model[is-reply]")

        for i, comment_container in enumerate(comment_containers):
            comment_id = f"{blog_id}_{parent_id}_{i}"
            username = comment_container.find_element(By.CSS_SELECTOR, "#header-author").text
            username = username.split('\n')[0] if username else username
            username = username.lstrip('@') if username else username
            content = comment_container.find_element(By.CSS_SELECTOR, "#content-text").text
            like_count_text = comment_container.find_element(By.CSS_SELECTOR, "#vote-count-middle").text
            like_count = parse_korean_number(like_count_text)  # 한글 숫자 변환
            published_date = comment_container.find_element(By.CSS_SELECTOR, "#published-time-text").text
            published_date = self.convert_youtube_time(published_date)

            replies.append({
                "id": comment_id,
                "username": username,
                "content": content,
                "blog_id": blog_id,
                "platform": "Youtube",
                "parent_id": parent_id,
                "published_date": published_date,
                "like_count": like_count,
                "star_count": None,
            })

        return replies

    def get_post(self, video_id, title, description, published_date, retry_count=3, driver=None, wait=None):
        """
        개별 동영상 정보 및 댓글 수집 + STT 전사

        Args:
            video_id: 동영상 ID
            title: 제목
            description: 설명
            published_date: 게시일
            retry_count: 재시도 횟수
            driver: 브라우저 인스턴스 (병렬 처리용, None이면 self.driver 사용)
            wait: WebDriverWait 인스턴스 (병렬 처리용, None이면 self.wait 사용)

        Returns:
            (post_data, comments)
        """
        # 브라우저 인스턴스 결정 (외부 전달 또는 기본)
        drv = driver or self.driver
        wt = wait or self.wait
        use_external_driver = driver is not None

        print(f"📝 get_post 호출: published_date = '{published_date}'")

        for attempt in range(retry_count):
            try:
                # 브라우저 상태 확인 (기본 드라이버 사용 시에만)
                if not use_external_driver:
                    self._check_browser()
                    drv = self.driver
                    wt = self.wait

                # 동영상 페이지 접근
                print(f"🔗 동영상 페이지 접근 중... (시도 {attempt + 1}/{retry_count})")
                drv.get(f"https://www.youtube.com/watch?v={video_id}")
                time.sleep(5)

                # 좋아요 수 추출 (한글 숫자 변환)
                like_count_text = wt.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#top-level-buttons-computed > segmented-like-dislike-button-view-model > yt-smartimation > div > div > like-button-view-model > toggle-button-view-model > button-view-model > button > div.yt-spec-button-shape-next__button-text-content"))
                ).text
                like_count = parse_korean_number(like_count_text)  # 한글 숫자 변환

                # 조회수 추출 (한글 숫자 변환)
                view_count_text = drv.find_element(By.CSS_SELECTOR, "#info > span:nth-child(1)").text
                view_count_text = view_count_text.replace("조회수", "").replace("회", "").strip()
                view_count = parse_korean_number(view_count_text)  # 한글 숫자 변환

                # 채널명 추출
                username = drv.find_element(By.CSS_SELECTOR, "#text > a").text

                # STT 전사 수행 (중지 요청 체크)
                transcribed_text = ""
                if self.stt_enabled and self.transcriber:
                    # 중지 요청 확인 (타임아웃 시 전사 스킵)
                    if self.stop_event and self.stop_event.is_set():
                        print(f"⏹️ 중지 요청 감지 - STT 전사 스킵: {video_id}")
                    else:
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        stt_result = self.transcriber.transcribe_video(video_url, video_id)

                        if stt_result['success']:
                            transcribed_text = stt_result['text']
                            print(f"✅ STT 성공: {len(transcribed_text)}자 전사됨")
                        else:
                            print(f"⚠️ STT 실패: {stt_result['error']}")

                # content 구성
                # 1. 제목
                # 2. 설명 (있으면)
                # 3. 전사 텍스트 (있으면)
                content_parts = [title]

                if description and description.strip() and str(description).lower() != 'nan':
                    content_parts.append(f"\n[설명]\n{description}")

                if transcribed_text:
                    content_parts.append(f"\n[음성 전사]\n{transcribed_text}")

                content = "\n".join(content_parts)

                post_data = {
                    "id": video_id,
                    "title": title,
                    "content": content,
                    "published_date": published_date,
                    "platform": "Youtube",
                    "link": f"https://www.youtube.com/watch?v={video_id}",
                    "view_count": view_count,
                    "like_count": like_count,
                    "user_id": username,
                    "stt_success": bool(transcribed_text),  # STT 성공 여부
                }

                print(f"📊 post_data 생성 완료: published_date = '{post_data['published_date']}'")

                # 댓글 수집 (외부 드라이버 전달)
                comments = self.get_comments(video_id, driver=drv)
                print(f"✅ 댓글 {len(comments)}개 수집 완료")

                return post_data, comments

            except Exception as e:
                print(f"⚠️ 시도 {attempt + 1} 실패: {str(e)}")
                if attempt < retry_count - 1:
                    print(f"🔄 {3}초 후 재시도...")
                    time.sleep(3)
                    # 브라우저 재시작 (기본 드라이버 사용 시에만)
                    if not use_external_driver:
                        self._init_browser()
                        drv = self.driver
                        wt = self.wait
                else:
                    print(f"❌ 모든 재시도 실패: {video_id}")
                    raise

    def run(self, keyword, max_posts, start_date=None, end_date=None, stop_event=None):
        """
        YouTube 크롤러 실행 (병렬 처리 적용)

        Args:
            keyword: 검색 키워드
            max_posts: 최대 게시글 수
            start_date: 시작일 (YYYY-MM-DD, 옵션)
            end_date: 종료일 (YYYY-MM-DD, 옵션)
            stop_event: 중지 이벤트 (threading.Event, 옵션)

        Returns:
            (post_data, comment_data)
        """
        self.stop_event = stop_event  # 인스턴스에 저장
        print(f"🚀 YouTube 크롤러 실행 시작: {keyword}")
        print(f"⚙️ 병렬 처리: {'활성화' if self.max_workers > 1 else '비활성화'} (워커 수: {self.max_workers})")
        print(f"🎤 STT: {'활성화' if self.stt_enabled else '비활성화'}")

        post_data = []
        comment_data = []

        # 동영상 검색
        videos = self.search_videos(keyword, start_date, end_date, max_posts)
        print(f"✅ 검색 완료: {len(videos)}개 동영상 발견")

        if len(videos) == 0:
            print("⚠️ 검색된 동영상이 없습니다.")
            return post_data, comment_data

        # 병렬 처리 여부 결정
        if self.max_workers <= 1:
            # 순차 처리 (기존 방식)
            print("ℹ️ 순차 처리 모드")
            for i, video in enumerate(videos):
                # 중지 요청 체크
                if self.stop_event and self.stop_event.is_set():
                    print("⏹️ 크롤링 중지 요청 감지 - YouTube 크롤러 종료")
                    break

                video_id = video["id"]["videoId"]
                title = video["snippet"]["title"]
                description = video["snippet"]["description"]
                published_date = video["snippet"]["publishedAt"]

                # ISO 8601 형식 변환
                original_date = published_date
                try:
                    dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                    published_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"🗓️ 날짜 변환: {original_date} → {published_date}")
                except Exception as e:
                    print(f"❌ 날짜 변환 실패: {original_date} - {str(e)}")

                print(f"📹 [{i+1}/{len(videos)}] 처리 중: {title[:50]}... (ID: {video_id})")

                try:
                    posts, comments = self.get_post(video_id, title, description, published_date)
                    post_data.append(posts)
                    comment_data.extend(comments)
                    print(f"✅ 완료: 댓글 {len(comments)}개 수집")

                    # 실시간 저장 콜백 호출 (DB에 즉시 저장)
                    if self.save_callback:
                        try:
                            saved = self.save_callback(posts, comments)
                            print(f"💾 DB 저장 완료: {saved}건")
                        except Exception as cb_err:
                            print(f"⚠️ DB 저장 콜백 오류: {cb_err}")
                    else:
                        save_to_json("Youtube", [posts], comments)
                except Exception as e:
                    print(f"❌ 동영상 처리 오류: {str(e)}")
                    continue
        else:
            # 병렬 처리
            print(f"⚡ 병렬 처리 모드 (최대 {self.max_workers}개 동시 실행)")

            def process_video(video_info):
                """개별 동영상 처리 함수 (독립 브라우저 사용)"""
                # 중지 요청 체크 (병렬 처리 시에도 적용)
                if self.stop_event and self.stop_event.is_set():
                    return (None, None, "중지 요청")

                i, video = video_info
                video_id = video["id"]["videoId"]
                title = video["snippet"]["title"]
                description = video["snippet"]["description"]
                published_date = video["snippet"]["publishedAt"]

                # ISO 8601 형식 변환
                try:
                    dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                    published_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass

                print(f"📹 [{i+1}/{len(videos)}] 처리 중: {title[:50]}... (ID: {video_id})")

                # 워커별 독립 브라우저 생성
                worker_driver = None
                worker_wait = None
                try:
                    worker_driver, worker_wait = self._create_browser()
                    print(f"🌐 [{i+1}/{len(videos)}] 워커 브라우저 생성 완료")

                    posts, comments = self.get_post(
                        video_id, title, description, published_date,
                        driver=worker_driver, wait=worker_wait
                    )
                    print(f"✅ [{i+1}/{len(videos)}] 완료: 댓글 {len(comments)}개 수집")
                    # 실시간 저장 콜백 호출 (DB에 즉시 저장)
                    if self.save_callback:
                        try:
                            saved = self.save_callback(posts, comments)
                            print(f"💾 [{i+1}/{len(videos)}] DB 저장 완료: {saved}건")
                        except Exception as cb_err:
                            print(f"⚠️ [{i+1}/{len(videos)}] DB 저장 콜백 오류: {cb_err}")
                    else:
                        save_to_json("Youtube", [posts], comments)
                    return (posts, comments, None)
                except Exception as e:
                    print(f"❌ [{i+1}/{len(videos)}] 동영상 처리 오류: {str(e)}")
                    return (None, None, str(e))
                finally:
                    # 워커 브라우저 정리
                    if worker_driver:
                        try:
                            worker_driver.quit()
                            print(f"🔒 [{i+1}/{len(videos)}] 워커 브라우저 종료")
                        except Exception:
                            pass

            # ThreadPoolExecutor로 병렬 처리
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(process_video, (i, v)): i for i, v in enumerate(videos)}

                for future in as_completed(futures):
                    idx = futures[future]
                    try:
                        posts, comments, error = future.result()
                        if error:
                            print(f"⚠️ 작업 {idx+1} 오류: {error}")
                        else:
                            post_data.append(posts)
                            comment_data.extend(comments)
                    except Exception as e:
                        print(f"❌ 작업 {idx+1} 예외: {str(e)}")

        print(f"🎯 최종 결과: 게시글 {len(post_data)}개, 댓글 {len(comment_data)}개")
        return post_data, comment_data

    def get_channel_videos(self, channel_url, start_date, end_date, max_posts):
        """
        채널 URL에서 동영상 목록 가져오기

        Args:
            channel_url: 채널 URL (예: https://www.youtube.com/@channelname)
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            max_posts: 최대 동영상 수

        Returns:
            videos: 동영상 목록
        """
        import re

        # 채널 ID 또는 핸들 추출
        channel_id = None

        # @handle 형식
        if '@' in channel_url:
            handle = channel_url.split('@')[1].split('/')[0].split('?')[0]
            # 핸들로 채널 ID 검색
            search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={handle}&maxResults=1&key={self._get_current_api_key()}"
            response = requests.get(search_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    channel_id = data['items'][0]['snippet']['channelId']
        # /channel/UC... 형식
        elif '/channel/' in channel_url:
            channel_id = channel_url.split('/channel/')[1].split('/')[0].split('?')[0]
        # /c/customname 형식
        elif '/c/' in channel_url:
            custom_name = channel_url.split('/c/')[1].split('/')[0].split('?')[0]
            search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={custom_name}&maxResults=1&key={self._get_current_api_key()}"
            response = requests.get(search_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    channel_id = data['items'][0]['snippet']['channelId']

        if not channel_id:
            print(f"❌ 채널 ID를 찾을 수 없음: {channel_url}")
            return []

        print(f"📺 채널 ID: {channel_id}")

        # 채널의 동영상 검색
        videos = []
        next_page_token = None

        while len(videos) < max_posts:
            params = {
                'part': 'snippet',
                'channelId': channel_id,
                'type': 'video',
                'order': 'date',
                'maxResults': min(50, max_posts - len(videos)),
                'key': self._get_current_api_key()
            }

            if start_date:
                params['publishedAfter'] = f"{start_date}T00:00:00Z"
            if end_date:
                params['publishedBefore'] = f"{end_date}T23:59:59Z"
            if next_page_token:
                params['pageToken'] = next_page_token

            search_url = "https://www.googleapis.com/youtube/v3/search"
            response = requests.get(search_url, params=params, timeout=10)

            if response.status_code != 200:
                print(f"❌ API 오류: {response.status_code}")
                break

            data = response.json()
            videos.extend(data.get('items', []))

            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break

        print(f"✅ 채널에서 {len(videos)}개 동영상 발견")
        return videos[:max_posts]

    def run_channel(self, channel_url, start_date, end_date, max_posts, stop_event=None):
        """
        채널 URL로 크롤링 실행

        Args:
            channel_url: 채널 URL
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            max_posts: 최대 게시글 수
            stop_event: 중지 이벤트 (threading.Event, 옵션)

        Returns:
            (post_data, comment_data)
        """
        self.stop_event = stop_event
        print(f"🚀 YouTube 채널 크롤러 실행 시작: {channel_url}")
        print(f"⚙️ 병렬 처리: {'활성화' if self.max_workers > 1 else '비활성화'} (워커 수: {self.max_workers})")
        print(f"🎤 STT: {'활성화' if self.stt_enabled else '비활성화'}")

        post_data = []
        comment_data = []

        # 채널 동영상 검색
        videos = self.get_channel_videos(channel_url, start_date, end_date, max_posts)
        print(f"✅ 검색 완료: {len(videos)}개 동영상 발견")

        if len(videos) == 0:
            print("⚠️ 검색된 동영상이 없습니다.")
            return post_data, comment_data

        # 순차 처리 (채널 크롤링은 순차로)
        for i, video in enumerate(videos):
            if self.stop_event and self.stop_event.is_set():
                print("⏹️ 크롤링 중지 요청 감지 - YouTube 크롤러 종료")
                break

            video_id = video["id"]["videoId"]
            title = video["snippet"]["title"]
            description = video["snippet"]["description"]
            published_date = video["snippet"]["publishedAt"]

            # ISO 8601 형식 변환
            try:
                dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                published_date = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass

            print(f"📹 [{i+1}/{len(videos)}] 처리 중: {title[:50]}... (ID: {video_id})")

            try:
                posts, comments = self.get_post(video_id, title, description, published_date)
                post_data.append(posts)
                comment_data.extend(comments)
                print(f"✅ 완료: 댓글 {len(comments)}개 수집")

                # 실시간 저장 콜백 호출 (DB에 즉시 저장)
                if self.save_callback:
                    try:
                        saved = self.save_callback(posts, comments)
                        print(f"💾 DB 저장 완료: {saved}건")
                    except Exception as cb_err:
                        print(f"⚠️ DB 저장 콜백 오류: {cb_err}")
                else:
                    save_to_json("Youtube", [posts], comments)
            except Exception as e:
                print(f"❌ 동영상 처리 오류: {str(e)}")
                continue

        print(f"🎯 최종 결과: 게시글 {len(post_data)}개, 댓글 {len(comment_data)}개")
        return post_data, comment_data


# 독립 실행 테스트
if __name__ == "__main__":
    print("="*80)
    print("YouTube 크롤러 STT 업그레이드 테스트")
    print("="*80)

    # 환경변수 확인
    print("\n📋 환경변수 확인:")
    print(f"  YOUTUBE_API_KEYS: {'✅ 설정됨' if os.getenv('YOUTUBE_API_KEYS') else '❌ 미설정'}")
    print(f"  YOUTUBE_STT_ENABLED: {os.getenv('YOUTUBE_STT_ENABLED', 'false')}")
    print(f"  WHISPER_MODEL_SIZE: {os.getenv('WHISPER_MODEL_SIZE', 'small')}")
    print(f"  WHISPER_DEVICE: {os.getenv('WHISPER_DEVICE', 'cpu')}")
    print(f"  YOUTUBE_MAX_WORKERS: {os.getenv('YOUTUBE_MAX_WORKERS', '3')}")

    # Whisper 설치 확인
    print(f"\n🔍 Whisper 설치 확인:")
    print(f"  faster-whisper: {'✅ 설치됨' if WHISPER_LIBRARY == 'faster-whisper' else '❌ 미설치'}")
    print(f"  openai-whisper: {'✅ 설치됨' if WHISPER_LIBRARY == 'openai-whisper' else '❌ 미설치'}")
    print(f"  yt-dlp: {'✅ 설치됨' if YTDLP_AVAILABLE else '❌ 미설치'}")

    if not WHISPER_AVAILABLE:
        print("\n⚠️ Whisper가 설치되지 않았습니다.")
        print("   설치: pip install faster-whisper")
        print("   또는: pip install openai-whisper")

    if not YTDLP_AVAILABLE:
        print("\n⚠️ yt-dlp가 설치되지 않았습니다.")
        print("   설치: pip install yt-dlp")

    # 크롤러 실행
    try:
        youtube_crawler = YoutubeCrawler()
        post_data, comments = youtube_crawler.run("마데카솔겔", "2025-09-01", "2025-09-25", 5)  # 테스트용 5개만

        print("\n" + "="*80)
        print("✅ 테스트 완료!")
        print(f"   수집된 게시글: {len(post_data)}개")
        print(f"   수집된 댓글: {len(comments)}개")

        # STT 성공 개수 확인
        if post_data:
            stt_success_count = sum(1 for p in post_data if p.get('stt_success', False))
            print(f"   STT 성공: {stt_success_count}/{len(post_data)}개")

        print("="*80)

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
