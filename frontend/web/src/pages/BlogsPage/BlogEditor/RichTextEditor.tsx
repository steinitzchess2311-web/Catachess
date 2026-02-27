/**
 * RichTextEditor - TipTap WYSIWYG editor with Markdown serialization
 *
 * Displays: formatted rich text (bold, italic, headings, lists, etc.)
 * Stores:   Markdown string (via tiptap-markdown extension)
 * Usage:    pass `value` (Markdown string) and `onChange` (receives Markdown string)
 */

import React, { useEffect } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { Markdown } from 'tiptap-markdown';

interface RichTextEditorProps {
  value: string;        // Markdown string
  onChange: (md: string) => void;
}

// ─── Toolbar button ────────────────────────────────────────────────────────────

interface ToolbarButtonProps {
  onClick: () => void;
  active?: boolean;
  disabled?: boolean;
  title: string;
  children: React.ReactNode;
}

const ToolbarButton: React.FC<ToolbarButtonProps> = ({ onClick, active, disabled, title, children }) => (
  <button
    type="button"
    onClick={onClick}
    disabled={disabled}
    title={title}
    style={{
      padding: '5px 9px',
      fontSize: '0.85rem',
      fontWeight: 600,
      border: '1px solid #e2e8f0',
      borderRadius: '5px',
      cursor: disabled ? 'not-allowed' : 'pointer',
      backgroundColor: active ? '#2563eb' : 'white',
      color: active ? 'white' : '#374151',
      transition: 'all 0.15s ease',
      lineHeight: 1.4,
      minWidth: '30px',
    }}
    onMouseEnter={(e) => {
      if (!active && !disabled) e.currentTarget.style.backgroundColor = '#f0f4ff';
    }}
    onMouseLeave={(e) => {
      if (!active) e.currentTarget.style.backgroundColor = active ? '#2563eb' : 'white';
    }}
  >
    {children}
  </button>
);

// ─── Main component ────────────────────────────────────────────────────────────

const RichTextEditor: React.FC<RichTextEditorProps> = ({ value, onChange }) => {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Markdown,
    ],
    content: value,   // tiptap-markdown parses Markdown automatically
    onUpdate({ editor }) {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        onChange((editor.storage as any).markdown.getMarkdown());
      } catch {
        // Fallback: if tiptap-markdown storage is unavailable, use HTML
        onChange(editor.getHTML());
      }
    },
  });

  // Sync external value changes (e.g. loading a different article for edit)
  useEffect(() => {
    if (!editor) return;
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const current = (editor.storage as any).markdown.getMarkdown();
      if (current !== value) editor.commands.setContent(value);
    } catch {
      // Storage not available yet; skip sync
    }
  }, [value, editor]);

  if (!editor) return null;

  return (
    <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
      {/* Toolbar */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '4px',
          padding: '8px 10px',
          borderBottom: '1px solid #e2e8f0',
          backgroundColor: '#f8fafc',
        }}
      >
        {/* Headings */}
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          active={editor.isActive('heading', { level: 1 })}
          title="Heading 1"
        >
          H1
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          active={editor.isActive('heading', { level: 2 })}
          title="Heading 2"
        >
          H2
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
          active={editor.isActive('heading', { level: 3 })}
          title="Heading 3"
        >
          H3
        </ToolbarButton>

        <Divider />

        {/* Inline marks */}
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleBold().run()}
          active={editor.isActive('bold')}
          title="Bold"
        >
          <b>B</b>
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleItalic().run()}
          active={editor.isActive('italic')}
          title="Italic"
        >
          <i>I</i>
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleStrike().run()}
          active={editor.isActive('strike')}
          title="Strikethrough"
        >
          <s>S</s>
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleCode().run()}
          active={editor.isActive('code')}
          title="Inline code"
        >
          {'<>'}
        </ToolbarButton>

        <Divider />

        {/* Lists */}
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          active={editor.isActive('bulletList')}
          title="Bullet list"
        >
          • List
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          active={editor.isActive('orderedList')}
          title="Ordered list"
        >
          1. List
        </ToolbarButton>

        <Divider />

        {/* Blocks */}
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
          active={editor.isActive('blockquote')}
          title="Blockquote"
        >
          " "
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          active={editor.isActive('codeBlock')}
          title="Code block"
        >
          {'{ }'}
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().setHorizontalRule().run()}
          title="Horizontal rule"
        >
          ─
        </ToolbarButton>

        <Divider />

        {/* History */}
        <ToolbarButton
          onClick={() => editor.chain().focus().undo().run()}
          disabled={!editor.can().undo()}
          title="Undo"
        >
          ↩
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().redo().run()}
          disabled={!editor.can().redo()}
          title="Redo"
        >
          ↪
        </ToolbarButton>
      </div>

      {/* Editor area */}
      <EditorContent
        editor={editor}
        style={{ padding: '14px 16px', minHeight: '320px', fontSize: '1rem', lineHeight: 1.7 }}
      />

      {/* Editor content styles */}
      <style>{`
        .tiptap { outline: none; }
        .tiptap h1 { font-size: 1.7rem; font-weight: 700; margin: 0.6em 0 0.3em; }
        .tiptap h2 { font-size: 1.35rem; font-weight: 600; margin: 0.6em 0 0.3em; }
        .tiptap h3 { font-size: 1.1rem; font-weight: 600; margin: 0.5em 0 0.2em; }
        .tiptap p  { margin: 0.4em 0; }
        .tiptap ul, .tiptap ol { padding-left: 1.4em; margin: 0.4em 0; }
        .tiptap li { margin: 0.15em 0; }
        .tiptap blockquote {
          border-left: 3px solid #2563eb;
          padding-left: 12px;
          margin: 0.5em 0;
          color: #475569;
        }
        .tiptap code {
          background: #f1f5f9;
          border-radius: 4px;
          padding: 2px 5px;
          font-family: monospace;
          font-size: 0.9em;
        }
        .tiptap pre {
          background: #1e293b;
          color: #e2e8f0;
          border-radius: 6px;
          padding: 12px 16px;
          overflow-x: auto;
          margin: 0.6em 0;
        }
        .tiptap pre code { background: none; color: inherit; padding: 0; }
        .tiptap hr { border: none; border-top: 1px solid #e2e8f0; margin: 1em 0; }
        .tiptap strong { font-weight: 700; }
        .tiptap em { font-style: italic; }
        .tiptap s { text-decoration: line-through; }
      `}</style>
    </div>
  );
};

const Divider = () => (
  <div style={{ width: '1px', backgroundColor: '#e2e8f0', margin: '2px 2px', alignSelf: 'stretch' }} />
);

export default RichTextEditor;
