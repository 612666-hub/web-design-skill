# 可直接复用的 CSS 模式

每个模式都给出完整代码，评审时整段替换即可，不要拆碎。

## 1. 响应式容器 + 自适应栅格

```css
.page {
  width: min(1120px, 100% - 2rem);
  margin-inline: auto;
}

.grid {
  display: grid;
  gap: 1.25rem;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

@media (max-width: 640px) {
  .grid { grid-template-columns: 1fr; }
}
```

`auto-fit + minmax` 的好处：窄屏自动降列，不需要写一堆断点。固定三栏改两栏时只写：

```css
@media (max-width: 960px) { .grid-3 { grid-template-columns: repeat(2, 1fr); } }
```

## 2. 一行一列都不塌的垂直居中

```css
.center {
  display: grid;
  place-items: center;
  min-height: 60vh;
}
```

不要再用 `position: absolute; top: 50%; margin-top: -Npx` 这类负外边距写法。

## 3. 粘性页脚（内容不足一屏时也贴底）

```css
body {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
main { flex: 1 0 auto; }
footer { flex-shrink: 0; }
```

## 4. 卡片组（等高、图文混排）

```css
.card {
  display: flex;
  flex-direction: column;
  border-radius: 12px;
  border: 1px solid #e2e6ec;
  background: #fff;
  overflow: hidden;
}
.card img {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
}
.card__body {
  padding: 1rem 1.125rem;
  display: flex;
  flex-direction: column;
  gap: .5rem;
  flex: 1;
}
.card__link { margin-top: auto; }   /* 让按钮统一贴底，卡片高度不一致也对齐 */
```

## 5. 视觉隐藏但仍可被读屏和搜索读到

```css
.sr-only {
  position: absolute;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
  border: 0;
}
```

## 6. 键盘可见的焦点轮廓

```css
:root { --focus: #0f766e; }

a:focus-visible,
button:focus-visible,
input:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 3px;
}
```

## 7. 图片不变形

```css
img { max-width: 100%; height: auto; }
.cover { aspect-ratio: 3 / 2; object-fit: cover; }
```

## 8. 长文本不撑破容器

```css
.text {
  overflow-wrap: anywhere;
  word-break: break-word;   /* 处理长英文串和 URL */
}
```

## 9. 断点约定

| 名称 | 宽度 | 用途 |
| --- | --- | --- |
| sm | ≤ 640px | 手机，单列 |
| md | ≤ 960px | 平板，两列 |
| lg | ≤ 1280px | 小笔记本，三列 |

写法统一用 `max-width` 的 `@media` 覆盖，从宽到窄依次声明，避免 `min-width` 和 `max-width` 混用导致的断点打架。

## 常用反例对照

| 反例 | 为什么错 | 改成 |
| --- | --- | --- |
| `float: left` + `clearfix` 做三栏 | 高度塌陷、间距难控 | `display: grid` |
| `margin-left: 273px` | 魔法数字，改字号就崩 | 用 `gap` 或 `calc()` 基于变量 |
| `outline: none` 去掉焦点框 | 键盘用户迷路 | `:focus-visible` 换成显式轮廓 |
| 正文 12px | 手机端不可读、缩放后错位 | 16px 起 | 
| `div` 加 `onclick` 当按钮 | 无键盘语义 | `<button type="button">` |
