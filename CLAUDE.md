# CLAUDE.md - 자동 패션 이미지 생성 시스템
## 기본 지침
**todo.md 또는 worksheet.md에 따라 한 단계씩 체크하면서 작업 진행하고, 해당 작업이 완료되면, 반드시 기록 업데이트 하라.사용자에게는 항상 한글로 답하라**
**절대 가짜 데이터나 가짜 로직을 사용하면 안된다!!**
**모든 프롬프트에 대한 작업을 진행하기 전에는 무조건 최소한 claude.md 중요 지침 및 150줄 까지의 내용과 worksheet.md 의 가장 최근 내용 최소 10개 및 최소 200줄 확인 필수**
**150줄 이후의 내용은 진행 상황과 개발 언어 및 개발 요소에 따라 필요한 부분을 찾아서 정확하게 파악하여 적용**
**반드시 사용자 편의성, 사용자 경험을 고려하고, 모든 기능과 데이터의 정확성, 효율성, 최적화, 완벽성, 완결성, 무결성, 호환성, 논리성을 추구**
**제한을 준수한다: 파일 ≤ 300 LOC, 함수 ≤ 50 LOC, 매개변수 ≤ 5, 순환 복잡도 ≤ 10. 초과 시 분리/리팩터링한다. 단, 복잡도를 높이면 안된다. 파이썬 모듈 파일명 규칙 우선 적용**
**항상 작업 전에는, 작업 관련한 내용에 대해서 기존 코드베이스를 완전하게 확인하고 파악해야 한다. 중복 작업이나 계속 새로운 파일 및 코드를 쓸데없이 만들지 말고, 기존 코드베이스를 확인하여 중복 작업을 피하고 효율적인 코드를 작성한다.**
**항상 작업 전에는, 계획(plan)과 할일(todo)을 검토하여야 한다. plan 폴더를 만들고, plan을 검토하며 만약 작업 중 사용자 요구 사항이나 상황에 따라 계획이 변경되면, 반드시 plan을 업데이트 하여 plan_번호.md 로 저장한다. plan_번호는 반드시 1씩 증가한다. plan에는 작성 날짜와 시간을 반드시 포함. plan에는 전체 프로그램의 구성과 구조, 의도 등이 명확해야 하며, 상세한 구현 계획 포함. 장기적인 미래 목표나 계획보다는 바로 구현이 필요한 내용 중심으로 작성**
**plan 폴더에는 todo 파일도 함께 존재. todo 파일에는 할일 목록이 체크리스트 형태로 기록되어 있으며, 할일이 완료되면 체크한다. 장기적인 내용보다는 바로 구현이 필요한 내용 중심으로 작성. plan이 변경되면 todo도 반드시 업데이트 한다. todo_번호.md 파일로 저장한다. todo_번호는 반드시 1씩 증가한다. todo에는 작성 날짜와 시간을 반드시 포함. 파일이나 프로그램을 검토할 때 또는 구현 내용을 테스트하거나 검증할 때는, 반드시 plan과 todo를 확인하여야 한다. 미구현 된 내용이 있는지 항상 확인한다. 구현 완료되었는데 체크되어 있지 않은 경우는 정확하게 다시 확인하여, 실행 여부를 체크!**
**사용자의 요구와 질문에 항상 논리적으로 생각하고 검토하여 의미 있는 응답을 할 것!**
**절대! 사용자 승인 없이 데이터베이스는 삭제하거나 지우지 말 것!!**
**절대 추측하지 말고, 정확한 상황과 내용을 파악하여 사실에 기반한 판단을 하라**
**지시하지 않은 문서는 작성하지 마라**
**반드시 모든 작업에서 백엔드, 프론트엔드 항상 함께 검토하라**

## 필수 작업 순서 (반드시 준수)
1. [ ] 핵심 구성 요소 점검 및 기대하는 기능 목록 구성
2. [ ] 해당 기능을 구현하기 위한 기술 문서 리서치 및 검색
3. [ ] 엣지 케이스 도출
4. [ ] 엣지 케이스 해결을 위한 기술 문서 리서치 및 검색
5. [ ] 새 브랜치 생성 및 스펙 문서 작성
6. [ ] 스펙에 따른 구현 방향 리서치 및 검색
7. [ ] 세션 메모리에 진행상태 저장
8. [ ] 스펙 및 세션메모리 기반으로 Draft PR 생성
9. [ ] 구현 시작 (반드시 백엔드, 프론트엔드 모두 작업)
10. [ ] 구현 완료 후 세션 메모리 업데이트
11. [ ] 새 세션 발생 시 이전 세션의 메모리 확인
12. [ ] 모든 구현 완료 및 스펙 완성 시 PR 업데이트 및 리뷰
13. [ ] 리뷰에서 나온 개선사항 모두 수정
14. [ ] 수정사항으로 인한 사이드 이펙트 추가리뷰 및 이전에 놓친 리뷰 확인
15. [ ] 수정 사항이 없을 때까지 반복적으로 수정 및 리뷰 반복
16. [ ] 최종 PR 업데이트 및 리뷰 대기 상태로 전환
17. [ ] 관련 이슈 코멘트 및 상태 업데이트

## 코드 수정 필수 규칙 (절대 위반 금지)
1. 수정 전: 데이터 생성→처리→표시 전체 흐름 끝까지 추적 (한 함수만 보지 마라)
2. 전역 검색: 같은 변수/함수명 전체 검색, 모든 사용처 동시 수정
3. 개수 세기: 컬럼/필드/파라미터 개수를 모든 곳에서 세어서 일치 확인
4. 타입 검증: numpy 인덱싱→int, pandas→Index, 딕셔너리→키 존재 확인
5. 영향도 분석: 이 수정이 다른 어디에 영향 주는지 체크 (import, 호출 체인)
6. 즉시 검증: 수정 직후 관련 코드 재검색, 구조 일치 재확인
7. 금지: "여기만 고치면 되겠지" / "비슷하니까 괜찮겠지" / "일단 고치고 나중에 확인"
**위반 시 연쇄 오류 발생. 반드시 worksheet.md에 체크리스트 수행 여부 기록.**

## 테스트 규칙
**사용자가 명시적으로 테스트 방법을 지정하지 않을 경우, 모든 테스트는 실제로 코드를 실행하는 테스트 진행**
**모든 테스트는 사용자의 특별한 지시가 없을 경우, 무조건 실제 기능 테스트를 해야 한다. 단순 논리 테스트만 진행하면 안된다. 실제로 기능을 수행해야 한다. default test는 실제 기능 실행 테스트이다**
**각 테스트마다 실제 결과 로그를 보고. 실제로 API 호출했는지, 데이터 다운로드했는지, 계산 결과가 나왔는지 증명**
**테스트 실행 결과에서 실제 수행 내용을 캡처해서 보여줘. INFO 로그, 데이터 개수, 계산 결과를 모두 보고**
**모든 테스트에서 실제 실행 로그를 출력 및 보고**
**API 호출, 데이터 다운로드, 계산 결과 명시**
**테스트가 1-2초에 끝나면 의심하고 다시 확인**
**모든 테스트가 완료되면, 발생한 이슈와 문제를 디버그 계획에 따라 수정 진행하고, 수정이 완료되면, 다시 테스트 진행**
**전체 프로그램의 계획되고 의도된 파이프라인과 워크플로우에 따라 올바른 테스트 계획을 수립하고 테스트 실행하라**

## 코딩 규칙
**사용자의 지시를 명확하게 따르도록 하라. 그 어떤 당신의 생각보다도 가장 우선하라. 모든 내용을 모두 무시하고 사용자의 지시가 우선이다!**
**복잡한 예외처리 금지**
**사용자 지시 무시 시 즉시 중단**
**절대 조용한 오류 처리 금지**
**코드를 추측하지 말고, 직접 확인하라. 항상 정확하게 파악하고 답변하라**
**절대로 문제를 확대하지 마라! 핵심에 대해서만 작업하라!**
**파일은 처음부터 끝까지 철저히 읽는다(부분 읽기 금지).**
**1. TDD 원칙 (Test Driven Development): 기능 구현 전에 테스트를 먼저 작성하고,  통과시키기 위한 최소 코드를 작성하며, 그 후 리팩터링을 거치는 개발 방식. -> 버그 감소 & 조기 발견, 리팩토링에 용이**
**2. SRP 원칙 (단일 책임 원칙): 하나의 클래스(또는 모듈)는 오직 하나의 책임(변경 이유)만 가져야 한다는 원칙 -> 변경에 안전, 코드 재사용성 증가, 테스트 용이**
**3. OCP 원칙 (개방 - 폐쇄 원칙): 기능은 추가할 수 있어야 하지만, 기존 코드는 수정하지 않아야 함. -> 새로운 클래스 추가만으로 기능 확장이 용이, 신규 타입 추가 시 소스 수정 필요 없음.**
**4. LSP 원칙 (리스코프 치환 원칙):상속받은 객체가 부모의 규약을 깨면 안 된다는 원칙**
**5. ISP 원칙 (인터페이스 분리 원칙):인터페이스는 작고 구체적이어야 하고, 클라이언트가 필요없는 기능을 강제받아서는 안 된다. -> 필요없는 기능 추가 할 필요 없음**
**6. DIP 원칙 (의존성 역전 원칙): 상위 모듈은 하위 구현체에 의존하지 말고, 추상에 의존해야 한다는 원칙 -> 테스트 용이, 변경 시 영향 최소화**
**7. Repository 패턴: 애플리케이션의 도메인 계층에서 데이터 접근 세부사항을 숨기고, 일관된 인터페이스를 제공하여 데이터 저장소와 상호작용하도록 하는 패턴 -> 테스트 용이, 유지보수 향상**

**지적받은 정확한 부분만 수정. 최소 수정. 핵심집중**
**관련 없는 부분은 건드리지 않음**
**확실하지 않으면 사용자에게 먼저 물어보기**
**핵심에만 집중하여 작업**
**수정 요청 받은 것에만 집중하고, 다른 파트나 정상작동 하는 기능들은 사용자 요구가 없을 경우 절대 수정하지 않음**
**사용자의 의도를 명확하게 파악하고, 지시에 확실하게 따라도록 하라** 
**복잡하게 생각하지 말고, 핵심을 정확하게 해결할 수 있는 가장 간단하고 가장 효율적이고 가장 강력한 방안을 찾아라**
**반드시 기본 데이터 흐름부터 먼저 확인하라. 데이터 흐름, 데이터 흐름 연결점, 파이프라인, 워크플로우, 매개변수 등 가장 기본을 확인하라**
**항상 겸손한 자세로 당신이 틀릴 수 있다는 생각을 갖고, 제로 베이스 사고를 하라**
**절대 거짓 보고 하지 말 것**
**코드를 복잡하게 작성하지 말것! 오류를 감추기 위한 폴백 금지! 예외처리 단순화**
**수정 및 작업 완료 후에는 제로베이스에서 3번 이상 검증하라. 다양한 관점에서 검증하라. 반드시 엣지케이스 검증하라**

**절대로 오류를 회피하거나, 숨기는 방식으로 해결 하지 마라. 오류나 경고를 맞서서 정확하게 원인을 해결하라. 이 프로그램은 매우 정밀하고 섬세한 분석 프로그램이다. 잘못된 결과 값이 제공되면 안된다. 이를 감안하여, 절대로 오류 회피, 기본값 반환 금지!**
**문제가 발생하면, 원인을 완전하게 파악하라. 여러가지 다양한 관점으로 원인을 확실하게 추적하라. 문제가 보여지는 지점부터 데이터 흐름을 역추적하여 반드시 원인을 찾아내라**
**사용자의 어떤 지시를 무시했는지 구체적으로 기록, 반복되는 실수 패턴 추적**
**인공지능 모델은 사용자의 허락 없이는 절대로 수정하지 마라!!**
**이 프로그램은 모듈화, 클래스 구조, ORM, 레고블록 형식의 구조로 작성해야 한다. 새로운 기능을 만들거나 새로운 파일이나 함수를 생성해야 할 때는 이점을 반드시 고려하여 만들어야 한다**
**이 프로그램을 웹 버전 또는 앱 버전으로 구조 변경도 고려하고 있다. 그러므로 이러한 형태들로 고도화 및 마이그레이션을 매우 간단하게 전환하거나 확장할 수 있도록, 백엔드 및 프로트엔드와 같은 구조를 고민하고, 이러한 점을 감안하여야 한다. 즉 아키텍처를 만들거나 새로운 파일 또는 함수를 만들 때 반드시 감안하라**
**절대 mock 데이터를 생성하지 마라. mock 코드를 만들지 마라. 실행 가능한 실제 코드를 만들어야 한다**

**무엇이든 변경하기 전에, 호출/참조 경로를 포함하여 관련 파일을 처음부터 끝까지 읽는다.**
**비밀값을 커밋하거나 로그에 남기지 않는다; 모든 입력을 검증하고 출력은 인코딩/정규화한다.**
**섣부른 추상화를 피하고 의도를 드러내는 이름을 사용한다.**
**결정하기 전에 최소 두 가지 대안을 비교한다.**
**시니어 엔지니어처럼 생각한다.**
**추측으로 뛰어들거나 성급히 결론내리지 않는다.**
**항상 여러 접근을 평가하고, 장점/단점/위험을 각각 한 줄로 적은 뒤 가장 단순한 해법을 선택한다.**
**코드를 변경하기 전에 정의, 참조, 호출 지점, 관련 테스트, 문서/설정/플래그를 찾아 읽는다.**
**파일 전체를 읽지 않았다면 코드를 변경하지 않는다.**
**심볼을 수정하기 전에 전역 검색으로 사전/사후 조건을 파악하고, 영향도를 1–3줄로 남긴다.**
**명시적인 코드를 선호한다; 숨겨진 “매직” 금지.**
**구체적인 예외만 처리하고, 사용자에게 명확한 메시지를 제공한다.**
**테스트는 결정적이고 독립적이어야 하며, 외부 시스템은 가짜/계약(컨트랙트) 테스트로 대체한다.**
**동시성/락/재시도에서 비롯될 위험(중복, 데드락 등)을 선제적으로 평가한다.**
**클린코드를 위하여 의도를 드러내는 이름을 사용한다.**
**각 함수는 한 가지 일만 한다.**
**상수는 항상 심볼화한다(하드코딩 금지).**
**코드를 입력 → 처리 → 반환 구조로 구성한다.**
**실패는 구체적인 오류/메시지로 보고한다.**
**테스트는 사용 예제로도 동작하게 하고, 경계/실패 사례를 포함한다.**
**전체 문맥을 읽지 않고 코드를 수정하지 않는다.**
**비밀값을 노출하지 않는다.**
**실패나 경고를 무시하지 않는다.**
**근거 없는 최적화나 추상화를 도입하지 않는다.**
**광범위한 예외를 남용하지 않는다.**

## worksheet.md 작성 규칙
**단계별 작업이 완료될 때는 400자 이내, 3줄 이내로 worksheet.md 에 작업 내용을 정확하게 기록. 넘버링 할 것. 역순으로 기록. 업데이트할 것. 원인, 결과, 작업 내용을 정확하게 작성. 기존 내용을 지우는 것이 아니라, 누적 기록 하는 것. 최신 내용이 상단에 위치하는 것. 만약 대규모 오류 수정 또는 심각한 오류를 수정해야 하는 경우에는 500자 이상, 5줄 이내 상세하게 기록할 것**
**개별 단계 작업을 시작할 때는 150자 이내, 2줄 이내로 요구사항, 작업목적, 계획을 간략하게 작성하라. 최신 내용이 상단에 위치. 기존 내용 지우는 것이 아니다.**
**만약 worksheet 라인 수가 제한을 넘어가는 경우에는, 오래된 기록은 worksheet_old1... 이런 식으로 번호를 붙여서 별도 파일로 분리하여 기존 내용을 저장(백업)하고, worksheet.md 에는 항상 최신 내용을 유지하라**
**worksheet.md 수정 시 반드시 Read 먼저 실행**
**Edit로 상단에 새 내용 추가 (Write 사용 금지)**

## 이 프로젝트를 다룰 때는:
1. **반드시 기존코드 및 구조를 확인** - 기존 코드의 데이터 프로세스, 파이프라인을 완벽하게 이해
2. **최소 수정 원칙** 엄격 준수 - 오류 하나당 수정 하나
3. **기존 코드 패턴 유지** - 일관성 있는 개발
4. **철학적 사유 기반** - 단순 기능 구현이 아닌 깊이 있는 통찰력 제공
5. **KISS 원칙** - 복잡하게 만들지 말고 간단하게 해결
6. **추측 금지** - 실제 존재하는 코드만 기반으로 작업
7. **예외처리 최소화** - 오류는 명확하게 드러나도록

## code 작성시 프로세스
1. 작업을 위한 계획 수립 및 상세 계획 확인
2. 사용자의 의도를 확인하고, 의도에 맞게 계획 검토
3. 계획에 맞는 check list 방식의 todo list 작성 및 확인
4. 정확한 계획과 todo list 에 따라 코드 작성
5. **모든 phase 단계별로 코드 작성 및 각 단계별로 작성한 코드에 대한 정적 검증 3회 반드시 실시**
6. 정적 검증 3회에 대해 완전히 무결성 검증 완료 된 후 worksheet.md 에 기록, todo.md 에 현재 진행 상황 표시
7. 계획에 따른 작업이 끝난 경우, 제로베이스로 전체 코드 정적 검증 5회 실시. 3회 이상 연속으로 무결성 검증 완료 시 다음 단계 진행
8. 엣지케이스 5개 작성하여, 검증 진행
9. 테스트코드 5개 작성하여, 테스트 진행. 실제 기능 테스트 위주로 진행. 2회는 전체 기능 통합 테스트 진행.
10. 모든 검증 및 테스트를 90% 이상 통과할 경우에만 사용자에게 보고


# CLAUDE.md - Universal Development Guide

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Design Principles (STRICT)

1. **NO raw HTML elements** - Use UI library components only (MUI Surface/Box replaces div)
2. **200 lines max per file** - Aggressively split components into smaller files
3. **DRY everything** - Reusable components and hooks, never duplicate code
4. **Atomic Design** - Atoms → Molecules → Organisms → Templates
5. **Type-safe** - Full TypeScript, no `any` types allowed
6. **SSR First** - Use Next.js SSR/ISR for performance, minimize "use client"
7. **Component Composition** - Build complex from simple, prefer composition over inheritance
8. **Client Components Minimized** - Always prefer SSR, use "use client" sparingly
9. **NO FALLBACKS OR WORKAROUNDS** - Never use setTimeout, fallback patterns, or workarounds
10. **NO COMPROMISES** - Fix root causes, not symptoms. No shortcuts or band-aid solutions

## 📦 Package Manager

**CRITICAL: Always use the same package manager consistently**
- Check for `yarn.lock` → use `yarn`
- Check for `package-lock.json` → use `npm`
- **NEVER mix** npm and yarn in the same project

### Yarn Projects
```bash
yarn dev              # Start development server
yarn build            # Production build
yarn add <package>    # Install dependency
yarn remove <package> # Remove dependency
```

### NPM Projects
```bash
npm run dev           # Start development server
npm run build         # Production build
npm install <package> # Install dependency
npm uninstall <package> # Remove dependency
```

## 🏗️ Component Architecture

### File Size & Modularity
- **Keep files short**: Aim for <200 lines per component file
- **Single responsibility**: Each component should have one clear purpose
- **Extract when growing**: Split into smaller pieces when approaching 200 lines
- **Avoid monolithic components**: Break down complex UIs into composable parts

### Component Organization
```
src/
├── components/
│   ├── ui/              # Design system components (Button, Card, Input, Dialog)
│   ├── layout/          # Layout components (Header, Sidebar, Footer)
│   └── feature/         # Feature-specific components
├── lib/                 # Utility functions and configurations
├── hooks/               # Custom React hooks
└── types/               # TypeScript type definitions
```

## 🚀 SSR/Client Component Architecture

### Default: Server Components (Preferred)

**Server Component Pattern:**
```typescript
// components/organisms/EmailList/EmailList.tsx
// DEFAULT: No "use client" directive = Server Component
import { Surface, Text } from "@/components/atoms";

export function EmailList({ emails }: { emails: Email[] }) {
  return (
    <Surface>
      {emails.map((email) => (
        <EmailCard key={email.id} email={email} />
      ))}
    </Surface>
  );
}
```

### Client Components (Use Sparingly)

**When to Use "use client":**
- Event handlers (onClick, onSubmit, etc.)
- React state (useState, useReducer)
- React effects (useEffect, useLayoutEffect)
- Browser-only APIs (localStorage, window, document)
- Third-party libraries requiring client-side

**Minimal Client Component Pattern:**
```typescript
// components/atoms/InteractiveButton/InteractiveButton.tsx
"use client"; // ONLY when absolutely necessary

import { useState } from "react";
import { Button } from "@mui/material";

export function InteractiveButton({ onClick, ...props }) {
  const [loading, setLoading] = useState(false);

  const handleClick = async (event) => {
    setLoading(true);
    await onClick?.(event);
    setLoading(false);
  };

  return <Button {...props} onClick={handleClick} disabled={loading} />;
}
```

## 🔥 Hydration Error Prevention (CRITICAL)

**NEVER create hydration mismatches:**

### Forbidden Patterns:
- ❌ `Date.now()`, `Math.random()` or any non-deterministic values in render
- ❌ `typeof window !== 'undefined'` conditional rendering
- ❌ Browser-specific APIs in initial render (localStorage, sessionStorage)
- ❌ Invalid HTML nesting (divs in p tags, etc.)

### Required Patterns:
- ✅ Use `useEffect` for client-only code after hydration
- ✅ Use `useState` with consistent initial values across server/client
- ✅ Use `suppressHydrationWarning={true}` ONLY for unavoidable browser differences
- ✅ Use Next.js `dynamic()` with `ssr: false` for client-only components

### Example Safe Patterns:
```typescript
// ✅ Safe: Consistent across server/client
const [mounted, setMounted] = useState(false);
useEffect(() => setMounted(true), []);
if (!mounted) return <div>Loading...</div>;

// ✅ Safe: Client-only component
const ClientComponent = dynamic(() => import('./ClientOnly'), { ssr: false });

// ✅ Safe: Fixed seed values for demo data
const DEMO_SEEDS = [
  { id: 'demo-1', value: 123, date: '2024-01-01' },
  { id: 'demo-2', value: 456, date: '2024-01-02' }
];
```

## 📝 Development Workflow (MANDATORY)

### For Every Change:

1. **Code Review**: Review the changes you made
   - Check for code quality issues
   - Verify type safety
   - Ensure best practices are followed
   - Look for potential bugs or edge cases

2. **Build**: Run production build to catch errors
   ```bash
   yarn build  # or npm run build
   ```
   - Fix any TypeScript errors
   - Fix any build errors
   - Ensure all imports are correct

3. **Unit Tests**: Run tests if applicable
   ```bash
   yarn test  # or npm test
   ```

4. **Commit and Push**: Only after build succeeds
   ```bash
   git add .
   git commit -m "descriptive commit message"
   git push
   ```

**Why this is essential:**
- Catches TypeScript errors and build issues early
- Ensures deployment will succeed
- Validates all components compile correctly
- Prevents deployment failures
- Maintains code quality

**IMPORTANT**: Never skip the build step. If build fails, fix the errors before committing.

## 🔧 Git Workflow

**ALWAYS follow these steps for ALL changes:**
```bash
# 1. Review changes
git diff

# 2. Stage files
git add <files>

# 3. Commit with descriptive message
git commit -m "descriptive message"

# 4. Push to remote
git push
```

## 🔒 Firebase Integration Rules (If Applicable)

When adding any Firestore database calls:
1. **Always update Firestore security rules** in `firestore.rules`
2. **Document new collections/documents** in schema files
3. **Test rules locally** before deploying
4. **Deploy rules** with `firebase deploy --only firestore:rules`
5. **Never store sensitive data** in Firestore without encryption

### Data Schema Management (CRITICAL)
**Always update schema files when making Firestore-related changes:**

1. **Update Schema Files First**: Before implementing data changes, update schema files
2. **Reference Schema Files**: Always refer to schemas for consistency
3. **Document New Collections**: Create new schema files for new collections
4. **Maintain Backward Compatibility**: Ensure compatibility or plan migration
5. **Collection Paths**: Use exact paths as documented (e.g., `aiPersonas/{id}`, not `AIPersonas/{id}`)
6. **Field Names**: Match schema exactly, check required vs optional fields
7. **Data Types**: Follow TypeScript interface definitions strictly

### Firebase Functions Deployment
**IMPORTANT**: Deploy functions in the background. Do NOT run deployment during active development.

```bash
cd functions
npm run build  # or yarn build
firebase deploy --only functions
```

### Firebase Functions Best Practices
1. **1 File 1 Function Principle**: Each function in its own file for maintainability
2. **Module Naming**: Functions auto-prefix with module name (e.g., `ai-generateResponse`)
3. **Shared Utilities**: Extract common code to dedicated shared files
4. **Always use Firebase Functions 2.0 syntax** for new functions

## 📊 MUI v7 Grid Usage (If Using MUI)

**IMPORTANT**: MUI v7 uses `size` prop instead of breakpoint-specific props.

### Correct Usage:
```jsx
import { Grid } from "@mui/material";

// Use 'size' prop instead of direct breakpoint props
<Grid container spacing={3}>
  <Grid size={{ xs: 12, md: 6, lg: 4 }}>
    {/* Content */}
  </Grid>
</Grid>
```

### Migration Notes:
- Convert `xs={12} md={6}` → `size={{ xs: 12, md: 6 }}`
- Grid items no longer need the `item` prop
- All grids are items by default

## 🎨 Styling Approach

### Priority Order:
1. **UI Library components** (MUI, Radix UI, etc.) - Use component-specific styling props
2. **Tailwind utilities** for rapid prototyping and layout
3. **CSS Modules** for component-scoped styles
4. **Styled components** only when absolutely necessary

### Design Tokens:
- **Consistent colors**: Use theme tokens, never hardcoded hex values
- **Consistent spacing**: Use theme spacing scale
- **Consistent typography**: Use theme typography variants
- **Component variants**: Style variations through props, not separate components

## 🧪 Testing Strategy

### Component Testing
```bash
# Use React Testing Library + Jest
yarn add -D @testing-library/react @testing-library/jest-dom jest

# Test files next to components
Surface/
  ├── Surface.tsx
  ├── Surface.test.tsx
  └── index.ts
```

### Testing Requirements:
- **Unit tests** for all components
- **Coverage**: Aim for >80% test coverage
- **Test structure**: Place test files next to components
- **Fail-fast**: Tests must pass before build/commit

## 📚 Documentation

### Code Documentation:
- **JSDoc comments** for complex functions
- **README.md** in each major feature directory
- **Type definitions** with clear interfaces
- **Example usage** in component files

### Project Documentation:
- Maintain up-to-date README.md
- Document environment variables
- Document deployment process
- Keep CHANGELOG.md current

## 🏷️ Naming Conventions

### File & Folder Naming (CRITICAL for Linux Compatibility):
- **ALWAYS use lowercase** for all folders and files
- **Use kebab-case** for multi-word names (e.g., `ai-economic-order`, not `AIEconomicOrder`)
- **Never use PascalCase or camelCase** in file/folder names
- **This is required** for Linux deployment compatibility
- Apply to all new components, pages, and directories

## ⚠️ Critical Implementation Notes

### Zero Tolerance for Hacks:
- Never use `setTimeout` for state synchronization
- Never use `window.location.reload()` to fix state issues
- Never use fallback patterns to mask underlying problems
- Always identify and fix root causes

### Root-Level Problem Resolution (CRITICAL):
- **NEVER use frontend fallbacks or workarounds** - Fix the underlying data/backend issue
- **Fix data layer problems fundamentally** - Don't mask database inconsistencies with UI logic
- **Eliminate technical debt immediately** - Never create quick fixes that defer proper solutions
- **Address root causes, not symptoms** - If data is missing/incorrect, fix the data source
- **Database integrity first** - Ensure Firestore/database handles edge cases properly
- **No band-aid solutions** - Temporary fixes accumulate tech debt
- **Data validation at the source** - Implement validation in backend, not just frontend
- **Backend-first problem solving** - Check if issue stems from backend before frontend fixes

### AI Integration Best Practices:
- **ALWAYS USE AI FOR TEXT PROCESSING** - NEVER use keyword-based classification or rule-based processing
- **Always use AI (Gemini, etc.) for**: Email classification, summarization, text analysis
- **No exceptions** - Rules-based approaches are forbidden for text processing
- Secure API key management via environment variables
- Implement caching strategies to minimize API calls
- Robust error handling and backoff strategies for rate limits

### Proper State Management:
- Use React state correctly
- Use proper data fetching patterns (React Query, SWR, etc.)
- No polling, no forced state changes, no bypass patterns
- Implement proper error boundaries

### Performance Best Practices:
- Code splitting with dynamic imports
- Lazy loading for non-critical components
- Memoization for expensive calculations
- Optimize images with next/image or similar
- Monitor bundle size

## 🔗 Environment Variables

### Naming Convention:
- `NEXT_PUBLIC_*` for client-side variables (Next.js)
- All other variables are server-side only
- Never commit `.env.local` to git
- Provide `.env.example` template

### Required Variables (Template):
```env
# Firebase (if applicable)
NEXT_PUBLIC_FIREBASE_API_KEY=
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=
NEXT_PUBLIC_FIREBASE_PROJECT_ID=

# API Keys
GEMINI_API_KEY=
PERPLEXITY_API_KEY=

# App Config
NEXT_PUBLIC_APP_URL=
```

## 🚢 Deployment

### Pre-Deploy Checklist:
- [ ] All tests passing
- [ ] Build successful
- [ ] Environment variables configured
- [ ] Database rules updated (if applicable)
- [ ] Cost impact assessed
- [ ] Security review completed

### Deployment Commands:
```bash
# Frontend (example)
yarn build && yarn start

# Firebase (if applicable)
firebase deploy --only hosting
firebase deploy --only functions
firebase deploy --only firestore:rules
```

## 📈 Monitoring & Analytics

### Track Key Metrics:
- User engagement events
- Performance metrics (Core Web Vitals)
- Error rates and types
- API usage and costs

### Performance Monitoring:
```typescript
import { trace } from "firebase/performance";

const processTrace = trace("process_name");
processTrace.start();
// ... processing
processTrace.stop();
```

## 🔍 Debugging Best Practices

### Firebase Functions Debugging
Query logs for specific functions to avoid searching through all logs:

```bash
# Query logs for a specific function
gcloud functions logs read ai-generateAiResponse --region=us-central1 --limit=50

# Real-time log streaming
gcloud functions logs tail ai-generateAiResponse --region=us-central1

# Query with filters using Cloud Logging
gcloud logging read "(resource.type='cloud_function' resource.labels.function_name='ai-generateAiResponse')" --limit=50 --format="table(timestamp,severity,textPayload)"
```

**Function Error Debugging Steps:**
1. Check function exists and is deployed: `gcloud functions list --filter="name:FUNCTION_NAME"`
2. Verify function parameters match expected schema
3. Check for missing environment variables or secrets
4. Use specific function name filters to isolate relevant logs
5. Monitor real-time logs during function execution

### Hydration Issues Debugging:
1. Check browser extensions (ad blockers, etc.) that modify DOM
2. Use React DevTools Profiler to identify hydration mismatches
3. Compare server HTML vs client HTML in browser dev tools
4. Temporarily add `__NEXT_DISABLE_HYDRATION_WARNING=true` for debugging only

---

**Last Updated**: 2025-10-08

This guide consolidates best practices from multiple projects and should be adapted to your specific project needs.

## 📌 Quick Reference

### Before Starting Any Task:
1. ✅ Check package manager (yarn.lock or package-lock.json)
2. ✅ Review existing components before creating new ones
3. ✅ Consult schema files if working with data
4. ✅ Check for project-specific CLAUDE.md in repository

### Before Committing:
1. ✅ `git diff` - Review all changes
2. ✅ `yarn build` or `npm run build` - Verify build passes
3. ✅ `yarn test` or `npm test` - Run tests if available
4. ✅ Fix all errors before committing
5. ✅ Update schema/documentation if data structures changed

### When Deploying:
1. ✅ All tests passing
2. ✅ Build successful
3. ✅ Environment variables configured
4. ✅ Database rules updated (if applicable)
5. ✅ Security review completed
6. ✅ Cost impact assessed
