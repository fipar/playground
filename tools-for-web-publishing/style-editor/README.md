# StyleStudio 🎨
> Interactive, dual-pane WYSIWYG CSS style generator for semantic HTML documents.

StyleStudio lets you take any unstyled HTML document, visually customize its styling element-by-element (typography, colors, box model spacing, flexbox layout, borders, and shadows), and export the result as clean `style.css` or a standalone `index.html`.

---

## ⚡ Quick Start

You can run StyleStudio with any local static HTTP server. A convenience script is included:

```bash
# Option 1: Using the launcher script
./serve.sh

# Option 2: Using Python 3 directly
python3 -m http.server 8080

# Option 3: Using Node / npm
npm start
# or
npx serve -p 8080
```

Once running, open your browser at **[http://localhost:8080](http://localhost:8080)**.

---

## 🚀 Key Features

### 1. Dual-Pane WYSIWYG Workflow
- **Left Pane (Live Preview)**:
  - Renders your HTML in an isolated iframe.
  - **Inspect Mode**: Hovering highlights any element; clicking an element selects it and updates the style inspector.
  - **DOM Breadcrumbs**: View the complete hierarchy (e.g., `body > div.container > article.work > h1`). Clicking any ancestor breadcrumb segment instantly selects that parent container.
  - **Selector Targets**: Choose whether styles apply to the **Tag** (`h1`), **Class** (`.site-title`), **Compound Selector** (`.work h1`), **ID** (`#main`), or a **Custom Selector**.
  - **Pseudo-Class States**: Easily style `:hover`, `:focus`, and `:active` states.
  - **Responsive Viewports**: Switch between **Desktop** (100%), **Tablet** (768px), and **Mobile** (390px) viewports with one click.
  - **Draggable Splitter**: Drag the vertical divider to adjust pane widths.

### 2. Right Pane (Visual Style Controls)
- **Theme Starters**: 1-click presets including:
  - **Studio Dark**: Dark slate aesthetic matching the Studio Numerozzi portfolio (`#0f1117`, card surfaces, borders, soft drop shadows).
  - **Editorial**: Warm paper serif typography (Playfair Display & Merriweather).
  - **Clean Light**: Crisp modern SaaS UI styling.
  - **Cyber Terminal**: High-contrast monospace neon theme.
  - **Clean Reset**: Semantic baseline reset.
- **Typography**:
  - Font family (System UI, Serif, Monospace, plus Google Fonts like *Inter*, *Playfair Display*, *Merriweather*, *JetBrains Mono*, *Plus Jakarta Sans*, *Space Grotesk*, etc. with dynamic loading).
  - Font size (px, rem, em), line height, font weight (300 to 800), letter spacing.
  - Text color (swatch picker + hex code), alignment (left, center, right, justify), transform, and text decoration.
- **Background & Color**:
  - Background color picker, transparency, custom gradients, and quick color swatches.
- **Spacing (Interactive Visual Box Model)**:
  - Visual diagram for `margin`, `border`, and `padding` with inputs for top, right, bottom, and left.
  - "Link" buttons to apply spacing evenly across all four sides.
- **Layout & Flexbox**:
  - Display modes (`block`, `flex`, `grid`, `inline-block`, etc.).
  - Flex direction, wrap, justify-content, align-items, and gap controls.
  - Width, max-width, min-height, and overflow.
- **Borders & Radius**:
  - Border width, style (`solid`, `dashed`, `dotted`), color, and border-radius (slider + 0, 4px, 8px, 12px, 16px, Full pills).
- **Shadows & Effects**:
  - Box shadow presets (Soft, Elevated, Card, Glow) and custom shadow inputs.
  - Opacity slider, cursor styles, and CSS transitions.
- **Direct CSS Code Editor**:
  - A real-time CSS code box for the currently active selector. Type any CSS property directly, and changes synchronize bi-directionally with the visual controls.
- **Full Stylesheet Editor**:
  - Click **Full CSS** to view, edit, or copy the complete stylesheet.

### 3. File Input & Export Options
- **Load HTML**:
  - **Open HTML**: Upload any `.html` file from your computer.
  - **Paste HTML**: Paste raw markup directly.
  - **Load Samples**: 1-click access to the unstyled **Studio Numerozzi Portfolio**, a **Markdown Blog Post**, or **Web Components**.
  - **Start Unstyled**: Optional toggle that automatically strips existing `<style>` tags or inline styles from imported files so you can start with a clean slate.
- **Export**:
  - **Download `style.css`**: Standalone, clean, indented CSS stylesheet.
  - **Download HTML (Embedded CSS)**: Self-contained HTML file containing your CSS inside a `<style>` block.
  - **Download HTML (Linked CSS)**: Clean HTML referencing `<link rel="stylesheet" href="style.css">`.
  - **Copy CSS**: One-click copy to your clipboard.
  - **Save Project**: Exports your HTML and styling state as a `.json` backup.
- **Auto-Save & Undo/Redo**:
  - Automatically preserves your work in `localStorage`.
  - Full Undo (`Cmd/Ctrl+Z`) and Redo (`Cmd/Ctrl+Y`) support.

---

## 📁 Included Sample Files
- `samples/portfolio.html` — Clean unstyled HTML markup for the Studio Numerozzi portfolio.
- `samples/blog-post.html` — Long-form editorial typography layout.
- `samples/components.html` — Interactive UI components, cards grid, forms, and buttons.
