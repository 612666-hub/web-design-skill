# web-design-review · 网页设计跟做助手

「高级网页设计」课堂跟做用的自定义 Skill：把一个写好的 HTML 页面当成待评审作业，按 **结构 / 布局 / 可访问性 / 代码规范** 四条线体检，输出可直接照着改的清单和自评分。

> 计算机科学与技术专业 · 高级网页设计 · 自定义 Skill 实践

## 它能解决什么问题

| 场景 | 以前 | 用这个 Skill |
| --- | --- | --- |
| 作业自查 | 靠感觉，「应该没问题吧」 | 脚本跑一遍硬问题 + 清单过一遍软问题，给 100 分制评分 |
| 布局调不对 | 反复改 padding 试 | 定位是盒模型、层叠还是断点，直接给替换代码 |
| 提交前 | 忘了 alt、忘了 viewport | 固定五条硬性检查，缺一项即"必修" |

## 目录结构

```text
web-design-skill/
├── SKILL.md                      # Skill 本体：触发条件、工作流程、输出模板
├── README.md                     # 你正在看的这份
├── index.html                    # GitHub Pages 落地页（这个 Skill 的展示页）
├── assets/
│   └── style.css                 # 落地页样式，同时是"可复用页面骨架"的样例
├── references/
│   ├── layout-checklist.md       # 四维度检查清单 + 扣分口径
│   └── css-patterns.md           # 栅格 / 居中 / 粘性页脚 / 卡片组等模式
├── scripts/
│   └── check_page.py             # 零依赖体检脚本，输出 Markdown 报告
└── LICENSE
```

## 快速开始

```bash
# 1. 体检任意页面或整个目录
python scripts/check_page.py index.html
python scripts/check_page.py ./pages --md report.md

# 2. 把 SKILL.md 的内容当成给 AI 的说明书使用
#    触发语：帮我体检一下这个页面 / 这个布局为什么错
```

脚本只用 Python 标准库（`html.parser`），不需要装任何依赖，Python 3.8+ 即可运行。

## 硬性检查项（缺一项即必修）

1. `<!DOCTYPE html>` 是否存在
2. `<html lang="...">` 是否声明语言
3. `meta viewport` 是否为 `width=device-width, initial-scale=1`
4. 每个 `<img>` 是否都有 `alt`
5. 是否存在重复 `id`
6. HTML 标签是否正常闭合

## 输出长什么样

```markdown
## 页面体检：index.html
**自评分：78 / 100**（结构 24/30 · 布局 20/25 · 可访问性 14/25 · 规范 20/20）
### 必修
1. 第 12 行 img 缺少 alt → 改：<img src="hero.png" alt="课程封面">
```

## 发布于 GitHub Pages

仓库推上去后，在 **Settings → Pages** 里把 Source 选成 `Deploy from a branch`、分支 `main`、目录 `/ (root)`，等 1～2 分钟即可通过
`https://<用户名>.github.io/<仓库名>/` 访问 `index.html`。

## License

MIT
