"""
Crawler manager for GUI and easy access
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import threading
import logging

from .crawler_service import CrawlerService, CrawlProgress, ProgressCallback, CrawlerCancellationToken
from .base_crawler import CrawledItem
from .common import DataUtils, DateUtils

logger = logging.getLogger(__name__)


class CrawlerGUI:
    """크롤러 GUI"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Fashion AI Generator - Crawler Manager")
        self.root.geometry("1000x700")

        # 크롤러 서비스
        self.crawler_service = CrawlerService()
        self.cancel_token: Optional[CrawlerCancellationToken] = None
        self.current_crawl_thread: Optional[threading.Thread] = None

        # 결과 저장
        self.crawled_items: List[CrawledItem] = []

        # GUI 초기화
        self._create_widgets()
        self._load_history()

    def _create_widgets(self):
        """위젯 생성"""
        # 노트북 생성
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # 탭 1: 새 크롤링
        self._create_new_crawl_tab()

        # 탭 2: 크롤링 이력
        self._create_history_tab()

        # 탭 3: 설정
        self._create_settings_tab()

    def _create_new_crawl_tab(self):
        """새 크롤링 탭 생성"""
        self.new_crawl_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.new_crawl_frame, text="New Crawling")

        # 검색 조건 프레임
        search_frame = ttk.LabelFrame(self.new_crawl_frame, text="Search Conditions", padding=10)
        search_frame.pack(fill='x', padx=10, pady=5)

        # 키워드
        ttk.Label(search_frame, text="Keyword:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.keyword_entry = ttk.Entry(search_frame, width=50)
        self.keyword_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5)

        # 날짜 범위
        ttk.Label(search_frame, text="Start Date:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.start_date_entry = ttk.Entry(search_frame, width=20)
        self.start_date_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        self.start_date_entry.insert(0, (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))

        ttk.Label(search_frame, text="End Date:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.end_date_entry = ttk.Entry(search_frame, width=20)
        self.end_date_entry.grid(row=2, column=1, sticky='w', padx=5, pady=5)
        self.end_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # 날짜 선택 버튼
        ttk.Button(search_frame, text="Select", command=self._select_start_date).grid(row=1, column=2, padx=5)
        ttk.Button(search_frame, text="Select", command=self._select_end_date).grid(row=2, column=2, padx=5)

        # 크롤러 선택
        crawler_frame = ttk.LabelFrame(self.new_crawl_frame, text="Crawler Selection", padding=10)
        crawler_frame.pack(fill='x', padx=10, pady=5)

        self.crawler_vars = {}
        for i, crawler_name in enumerate(self.crawler_service.get_available_crawlers()):
            var = tk.BooleanVar(value=True)
            self.crawler_vars[crawler_name] = var
            ttk.Checkbutton(
                crawler_frame,
                text=crawler_name,
                variable=var
            ).grid(row=i // 3, column=i % 3, sticky='w', padx=5, pady=2)

        # 제어 버튼
        control_frame = ttk.Frame(self.new_crawl_frame)
        control_frame.pack(fill='x', padx=10, pady=10)

        self.start_button = ttk.Button(control_frame, text="Start Crawling", command=self._start_crawling)
        self.start_button.pack(side='left', padx=5)

        self.stop_button = ttk.Button(control_frame, text="Stop Crawling", command=self._stop_crawling, state='disabled')
        self.stop_button.pack(side='left', padx=5)

        self.save_button = ttk.Button(control_frame, text="Save Results", command=self._save_results, state='disabled')
        self.save_button.pack(side='left', padx=5)

        # 진행 상태
        status_frame = ttk.LabelFrame(self.new_crawl_frame, text="Status", padding=10)
        status_frame.pack(fill='x', padx=10, pady=5)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(anchor='w')

        self.progress_var = tk.StringVar(value="Progress: 0%")
        ttk.Label(status_frame, textvariable=self.progress_var).pack(anchor='w')

        # 진행률 바
        self.progress_bar = ttk.Progressbar(status_frame, mode='determinate')
        self.progress_bar.pack(fill='x', pady=5)

        # 결과 미리보기
        preview_frame = ttk.LabelFrame(self.new_crawl_frame, text="Preview", padding=10)
        preview_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # 트리뷰
        columns = ('Platform', 'Title', 'Date', 'Score')
        self.results_tree = ttk.Treeview(preview_frame, columns=columns, show='headings', height=10)

        # 컬럼 설정
        self.results_tree.heading('Platform', text='Platform')
        self.results_tree.heading('Title', text='Title')
        self.results_tree.heading('Date', text='Date')
        self.results_tree.heading('Score', text='Quality Score')

        self.results_tree.column('Platform', width=100)
        self.results_tree.column('Title', width=300)
        self.results_tree.column('Date', width=100)
        self.results_tree.column('Score', width=100)

        # 스크롤바
        scrollbar = ttk.Scrollbar(preview_frame, orient='vertical', command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)

        self.results_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def _create_history_tab(self):
        """크롤링 이력 탭 생성"""
        self.history_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.history_frame, text="Crawling History")

        # 이력 목록
        history_list_frame = ttk.LabelFrame(self.history_frame, text="History", padding=10)
        history_list_frame.pack(fill='x', padx=10, pady=5)

        columns = ('Date', 'Keyword', 'Crawlers', 'Items', 'Duration')
        self.history_tree = ttk.Treeview(history_list_frame, columns=columns, show='headings', height=15)

        self.history_tree.heading('Date', text='Date')
        self.history_tree.heading('Keyword', text='Keyword')
        self.history_tree.heading('Crawlers', text='Crawlers')
        self.history_tree.heading('Items', text='Items')
        self.history_tree.heading('Duration', text='Duration')

        self.history_tree.column('Date', width=150)
        self.history_tree.column('Keyword', width=150)
        self.history_tree.column('Crawlers', width=200)
        self.history_tree.column('Items', width=80)
        self.history_tree.column('Duration', width=80)

        self.history_tree.pack(fill='x', pady=5)

        # 버튼
        history_button_frame = ttk.Frame(self.history_frame)
        history_button_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(history_button_frame, text="Load Selected", command=self._load_history_item).pack(side='left', padx=5)
        ttk.Button(history_button_frame, text="Delete Selected", command=self._delete_history_item).pack(side='left', padx=5)
        ttk.Button(history_button_frame, text="Clear History", command=self._clear_history).pack(side='left', padx=5)

    def _create_settings_tab(self):
        """설정 탭 생성"""
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")

        # 크롤러 설정
        crawler_settings_frame = ttk.LabelFrame(self.settings_frame, text="Crawler Settings", padding=10)
        crawler_settings_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(crawler_settings_frame, text="Max Workers:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.max_workers_var = tk.StringVar(value=str(self.crawler_service.max_workers))
        ttk.Spinbox(crawler_settings_frame, from_=1, to=10, textvariable=self.max_workers_var).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(crawler_settings_frame, text="Max Items per Crawler:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.max_items_var = tk.StringVar(value="100")
        ttk.Spinbox(crawler_settings_frame, from_=10, to=1000, textvariable=self.max_items_var).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(crawler_settings_frame, text="Delay (seconds):").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.delay_var = tk.StringVar(value="1")
        ttk.Spinbox(crawler_settings_frame, from_=0, to=10, textvariable=self.delay_var).grid(row=2, column=1, padx=5, pady=5)

        # 저장 경로
        save_frame = ttk.LabelFrame(self.settings_frame, text="Save Settings", padding=10)
        save_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(save_frame, text="Default Save Path:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.save_path_var = tk.StringVar(value="./crawled_data")
        self.save_path_entry = ttk.Entry(save_frame, textvariable=self.save_path_var, width=50)
        self.save_path_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(save_frame, text="Browse", command=self._browse_save_path).grid(row=0, column=2, padx=5, pady=5)

    def _select_start_date(self):
        """시작일 선택"""
        self._select_date(self.start_date_entry)

    def _select_end_date(self):
        """종료일 선택"""
        self._select_date(self.end_date_entry)

    def _select_date(self, entry):
        """날짜 선택"""
        import calendar
        from tkinter import simpledialog

        # 날짜 입력 다이얼로그
        dialog = simpledialog.askstring("Select Date", "Enter date (YYYY-MM-DD):")
        if dialog:
            try:
                DateUtils.parse_date_string(dialog)
                entry.delete(0, tk.END)
                entry.insert(0, dialog)
            except:
                messagebox.showerror("Error", "Invalid date format")

    def _start_crawling(self):
        """크롤링 시작"""
        # 입력값 확인
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showerror("Error", "Please enter a keyword")
            return

        start_date_str = self.start_date_entry.get().strip()
        end_date_str = self.end_date_entry.get().strip()

        try:
            start_date = DateUtils.parse_date_string(start_date_str) if start_date_str else None
            end_date = DateUtils.parse_date_string(end_date_str) if end_date_str else None
        except:
            messagebox.showerror("Error", "Invalid date format")
            return

        # 선택된 크롤러
        enabled_crawlers = [
            name for name, var in self.crawler_vars.items()
            if var.get()
        ]

        if not enabled_crawlers:
            messagebox.showerror("Error", "Please select at least one crawler")
            return

        # GUI 상태 업데이트
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_var.set("Crawling...")
        self.results_tree.delete(*self.results_tree.get_children())

        # 크롤러 설정 업데이트
        for name, crawler in self.crawler_service.crawlers.items():
            crawler.config.update({
                'max_items': int(self.max_items_var.get()),
                'delay': float(self.delay_var.get())
            })

        # 진행률 콜백
        progress_callback = ProgressCallback(self._update_progress)

        # 취소 토큰 생성
        self.cancel_token = CrawlerCancellationToken()

        # 스레드에서 크롤링 실행
        self.current_crawl_thread = threading.Thread(
            target=self._run_crawling_thread,
            args=(keyword, start_date, end_date, enabled_crawlers, progress_callback)
        )
        self.current_crawl_thread.daemon = True
        self.current_crawl_thread.start()

    def _run_crawling_thread(
        self,
        keyword: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        enabled_crawlers: List[str],
        progress_callback: ProgressCallback
    ):
        """크롤링 스레드 실행"""
        import asyncio

        try:
            # 비동기 크롤링 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            self.crawled_items = loop.run_until_complete(
                self.crawler_service.crawl_all(
                    keyword=keyword,
                    start_date=start_date,
                    end_date=end_date,
                    enabled_crawlers=enabled_crawlers,
                    progress_callback=progress_callback,
                    cancel_token=self.cancel_token
                )
            )

            # GUI 업데이트
            self.root.after(0, self._crawling_completed)

        except Exception as e:
            self.root.after(0, lambda: self._crawling_failed(str(e)))

    def _update_progress(self, progress: CrawlProgress):
        """진행률 업데이트"""
        self.progress_var.set(f"Progress: {progress.progress_percent:.1f}% ({progress.current_crawler})")
        self.progress_bar['value'] = progress.progress_percent

        if progress.status.value == "cancelled":
            self.status_var.set("Cancelled")

    def _stop_crawling(self):
        """크롤링 중지"""
        if self.cancel_token:
            self.cancel_token.cancel("User stopped crawling")
            self.status_var.set("Stopping...")

    def _crawling_completed(self):
        """크롤링 완료 처리"""
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.save_button.config(state='normal')
        self.status_var.set(f"Completed: {len(self.crawled_items)} items collected")

        # 결과 트리에 추가
        for item in self.crawled_items[:100]:  # 최대 100개만 표시
            self.results_tree.insert(
                '',
                'end',
                values=(
                    item.platform,
                    item.title[:50] + '...' if len(item.title) > 50 else item.title,
                    item.date.strftime("%Y-%m-%d") if item.date else '',
                    f"{item.quality_score:.2f}"
                )
            )

        # 이력 저장
        self._save_history()

    def _crawling_failed(self, error_msg: str):
        """크롤링 실패 처리"""
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_var.set(f"Failed: {error_msg}")
        messagebox.showerror("Error", f"Crawling failed: {error_msg}")

    def _save_results(self):
        """결과 저장"""
        if not self.crawled_items:
            messagebox.showwarning("Warning", "No data to save")
            return

        # 저장 위치 선택
        default_path = os.path.join(self.save_path_var.get(), f"crawled_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=default_path
        )

        if filepath:
            # 디렉토리 생성
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # 데이터 변환 및 저장
            data = [item.to_dict() for item in self.crawled_items]
            if DataUtils.save_to_json(data, filepath):
                messagebox.showinfo("Success", f"Results saved to {filepath}")
            else:
                messagebox.showerror("Error", "Failed to save results")

    def _browse_save_path(self):
        """저장 경로 탐색"""
        path = filedialog.askdirectory(initialdir=self.save_path_var.get())
        if path:
            self.save_path_var.set(path)

    def _save_history(self):
        """크롤링 이력 저장"""
        history = self._load_history_data()

        # 새 이력 추가
        history_item = {
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'keyword': self.keyword_entry.get(),
            'crawlers': [name for name, var in self.crawler_vars.items() if var.get()],
            'items_count': len(self.crawled_items),
            'duration': "N/A",
            'items': [item.to_dict() for item in self.crawled_items[:10]]  # 처음 10개만 저장
        }

        history.append(history_item)

        # 파일 저장
        history_file = os.path.join(self.save_path_var.get(), "crawling_history.json")
        DataUtils.save_to_json(history, history_file)

    def _load_history(self):
        """크롤링 이력 로드"""
        history_file = os.path.join(self.save_path_var.get(), "crawling_history.json")
        if os.path.exists(history_file):
            data = DataUtils.load_from_json(history_file)
            if data:
                for item in data:
                    self.history_tree.insert(
                        '',
                        'end',
                        values=(
                            item['date'],
                            item['keyword'],
                            ', '.join(item['crawlers']),
                            item['items_count'],
                            item['duration']
                        )
                    )

    def _load_history_data(self) -> List[dict]:
        """이력 데이터 로드"""
        history_file = os.path.join(self.save_path_var.get(), "crawling_history.json")
        return DataUtils.load_from_json(history_file) or []

    def _load_history_item(self):
        """선택된 이력 아이템 로드"""
        selection = self.history_tree.selection()
        if not selection:
            return

        item_id = selection[0]
        values = self.history_tree.item(item_id)['values']

        # 이력 데이터 로드
        history_data = self._load_history_data()
        for item in history_data:
            if item['date'] == values[0] and item['keyword'] == values[1]:
                # 데이터 채우기
                self.keyword_entry.delete(0, tk.END)
                self.keyword_entry.insert(0, item['keyword'])

                # 크롤러 선택
                for name in self.crawler_vars:
                    self.crawler_vars[name].set(name in item['crawlers'])

                # 결과 로드
                self.crawled_items = [CrawledItem(**item_dict) for item_dict in item.get('items', [])]
                self._crawling_completed()
                break

    def _delete_history_item(self):
        """선택된 이력 아이템 삭제"""
        selection = self.history_tree.selection()
        if not selection:
            return

        # 이력 데이터 로드 및 삭제
        history_data = self._load_history_data()
        values = self.history_tree.item(selection[0])['values']

        history_data = [
            item for item in history_data
            if not (item['date'] == values[0] and item['keyword'] == values[1])
        ]

        # 다시 저장
        history_file = os.path.join(self.save_path_var.get(), "crawling_history.json")
        DataUtils.save_to_json(history_data, history_file)

        # 트리에서 삭제
        self.history_tree.delete(selection)

    def _clear_history(self):
        """이력 초기화"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all history?"):
            history_file = os.path.join(self.save_path_var.get(), "crawling_history.json")
            if os.path.exists(history_file):
                os.remove(history_file)

            self.history_tree.delete(*self.history_tree.get_children())

    def run(self):
        """GUI 실행"""
        self.root.mainloop()


def main():
    """메인 함수"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    gui = CrawlerGUI()
    gui.run()


if __name__ == "__main__":
    main()