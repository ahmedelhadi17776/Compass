import { useEditor, EditorContent, type Editor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import TaskItem from '@tiptap/extension-task-item'
import TaskList from '@tiptap/extension-task-list'
import TextAlign from '@tiptap/extension-text-align'
import Typography from '@tiptap/extension-typography'
import Highlight from '@tiptap/extension-highlight'
import Subscript from '@tiptap/extension-subscript'
import Superscript from '@tiptap/extension-superscript'
import Underline from '@tiptap/extension-underline'
import { cn } from '@/lib/utils'
import EditorBubbleMenu from './EditorBubbleMenu'
import './task-list.css'

interface TiptapEditorProps {
  content: string
  onChange?: (content: string) => void
  editable?: boolean
  className?: string
}

const TiptapEditor = ({ content, onChange, editable = true, className }: TiptapEditorProps) => {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Image,
      TaskList.configure({
        HTMLAttributes: {
          class: 'not-prose pl-0',
        },
      }),
      TaskItem.configure({
        nested: true,
        HTMLAttributes: {
          class: 'flex gap-2 items-start my-1',
        },
      }),
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
      Typography,
      Highlight.configure({ multicolor: true }),
      Subscript,
      Superscript,
      Underline,
    ],
    content,
    editable,
    onUpdate: ({ editor }) => {
      onChange?.(editor.getHTML())
    },
    editorProps: {
      attributes: {
        autocomplete: 'off',
        autocorrect: 'off',
        autocapitalize: 'off',
        'aria-label': 'Main content area, start typing to enter text.',
      },
    },
  })

  if (!editor) {
    return null
  }

  return (
    <div className={cn("", className)}>
      <EditorBubbleMenu editor={editor} />
      <div className={cn(
        'prose prose-sm max-w-none',
        'prose-headings:text-white prose-p:text-white prose-strong:text-white prose-em:text-white prose-li:text-white',
        'prose-h1:text-3xl prose-h1:font-bold prose-h1:mb-6',
        'prose-h2:text-2xl prose-h2:font-semibold prose-h2:mb-4',
        'prose-h3:text-xl prose-h3:font-medium prose-h3:mb-3',
        'prose-p:mb-4 prose-p:text-white prose-p:text-base',
        'prose-ul:mb-4 prose-li:mb-2 prose-li:text-white prose-li:text-base',
        'prose-blockquote:border-l-4 prose-blockquote:border-white/50 prose-blockquote:pl-4 prose-blockquote:italic prose-blockquote:text-white',
        'prose-code:text-white prose-code:bg-gray-800/50 prose-code:rounded prose-code:px-1',
        '[&_*]:transition-colors [&_*]:duration-200',
        '[&_p]:!text-white [&_li]:!text-white [&_div]:!text-white',
        '[&_ul[data-type="taskList"]_li_div_p]:!text-white',
        '[&_ul[data-type="taskList"]_li_div_p]:!text-base',
        '[&_ul[data-type="taskList"]_li_div]:text-base'
      )}>
        <EditorContent editor={editor} />
      </div>
    </div>
  )
}

export default TiptapEditor 