# Project Rules — OnePal

## Security Boundaries
- 不要修改 OpenCode/ 目录
- 不要读取或输出 API Key、token、密码、私密凭证
- 不要触碰公司文件、凭证或私有数据
- 不要永久修改全局环境变量（如需必须确认）
- secrets/ 目录、*.key、*.token、*.env 文件均在 .gitignore 中排除

## Dev Workflow
- 默认先 Plan 分析，再 Build 执行
- 复杂任务先写简短实施方案
- 优先使用 HTML/CSS/JS 原型，再考虑引入框架
- 小步修改，每次验证后再继续
- 涉及系统命令、安装依赖、删除文件、联网请求、修改文件时必须先询问
- 每次修改后说明改了什么、怎么测试
- 需要长期记忆时，先生成 Memory Update Proposal，等待确认后再写入 memory/ 文件
- 高风险操作必须进入 approval queue
