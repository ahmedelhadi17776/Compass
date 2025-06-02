import { BubbleMenu, Editor } from '@tiptap/react'
import { Button } from "@/components/ui/button"
import {
  Bold,
  Italic,
  Strikethrough,
  List,
  ListOrdered,
  AlignLeft,
  AlignCenter,
  AlignRight,
  AlignJustify,
  Heading1,
  Heading2,
  Heading3,
  CheckSquare,
  Code,
  Quote,
  Highlighter,
  Subscript,
  Superscript,
  Underline,
  LucideIcon
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface EditorBubbleMenuProps {
  editor: Editor
}

type MenuItem = {
  icon: LucideIcon;
  title: string;
  action: () => void;
  isActive: () => boolean;
} | {
  type: 'divider';
}

export default function EditorBubbleMenu({ editor }: EditorBubbleMenuProps) {
  if (!editor) {
    return null
  }

  const items: MenuItem[] = [
    {
      icon: Bold,
      title: 'Bold',
      action: () => editor.chain().focus().toggleBold().run(),
      isActive: () => editor.isActive('bold'),
    },
    {
      icon: Italic,
      title: 'Italic',
      action: () => editor.chain().focus().toggleItalic().run(),
      isActive: () => editor.isActive('italic'),
    },
    {
      icon: Strikethrough,
      title: 'Strike',
      action: () => editor.chain().focus().toggleStrike().run(),
      isActive: () => editor.isActive('strike'),
    },
    {
      icon: Code,
      title: 'Code',
      action: () => editor.chain().focus().toggleCode().run(),
      isActive: () => editor.isActive('code'),
    },
    {
      icon: Underline,
      title: 'Underline',
      action: () => editor.chain().focus().toggleUnderline().run(),
      isActive: () => editor.isActive('underline'),
    },
    {
      type: 'divider',
    },
    {
      icon: Heading1,
      title: 'Heading 1',
      action: () => editor.chain().focus().toggleHeading({ level: 1 }).run(),
      isActive: () => editor.isActive('heading', { level: 1 }),
    },
    {
      icon: Heading2,
      title: 'Heading 2',
      action: () => editor.chain().focus().toggleHeading({ level: 2 }).run(),
      isActive: () => editor.isActive('heading', { level: 2 }),
    },
    {
      icon: Heading3,
      title: 'Heading 3',
      action: () => editor.chain().focus().toggleHeading({ level: 3 }).run(),
      isActive: () => editor.isActive('heading', { level: 3 }),
    },
    {
      type: 'divider',
    },
    {
      icon: List,
      title: 'Bullet List',
      action: () => editor.chain().focus().toggleBulletList().run(),
      isActive: () => editor.isActive('bulletList'),
    },
    {
      icon: ListOrdered,
      title: 'Ordered List',
      action: () => editor.chain().focus().toggleOrderedList().run(),
      isActive: () => editor.isActive('orderedList'),
    },
    {
      icon: CheckSquare,
      title: 'Task List',
      action: () => editor.chain().focus().toggleTaskList().run(),
      isActive: () => editor.isActive('taskList'),
    },
    {
      type: 'divider',
    },
    {
      icon: AlignLeft,
      title: 'Align Left',
      action: () => editor.chain().focus().setTextAlign('left').run(),
      isActive: () => editor.isActive({ textAlign: 'left' }),
    },
    {
      icon: AlignCenter,
      title: 'Align Center',
      action: () => editor.chain().focus().setTextAlign('center').run(),
      isActive: () => editor.isActive({ textAlign: 'center' }),
    },
    {
      icon: AlignRight,
      title: 'Align Right',
      action: () => editor.chain().focus().setTextAlign('right').run(),
      isActive: () => editor.isActive({ textAlign: 'right' }),
    },
    {
      icon: AlignJustify,
      title: 'Align Justify',
      action: () => editor.chain().focus().setTextAlign('justify').run(),
      isActive: () => editor.isActive({ textAlign: 'justify' }),
    },
    {
      type: 'divider',
    },
    {
      icon: Highlighter,
      title: 'Highlight',
      action: () => editor.chain().focus().toggleHighlight().run(),
      isActive: () => editor.isActive('highlight'),
    },
    {
      icon: Subscript,
      title: 'Subscript',
      action: () => editor.chain().focus().toggleSubscript().run(),
      isActive: () => editor.isActive('subscript'),
    },
    {
      icon: Superscript,
      title: 'Superscript',
      action: () => editor.chain().focus().toggleSuperscript().run(),
      isActive: () => editor.isActive('superscript'),
    },
    {
      type: 'divider',
    },
    {
      icon: Quote,
      title: 'Quote',
      action: () => editor.chain().focus().toggleBlockquote().run(),
      isActive: () => editor.isActive('blockquote'),
    },
  ]

  return (
    <BubbleMenu 
      className="flex flex-wrap gap-1 p-2 rounded-lg border bg-black/90 shadow-xl backdrop-blur-sm" 
      editor={editor}
      tippyOptions={{ duration: 100 }}
    >
      {items.map((item, index) => {
        if ('type' in item && item.type === 'divider') {
          return <div key={index} className="w-px h-6 bg-gray-700 mx-1 my-auto" />;
        }
        
        if ('icon' in item) {
          const Icon = item.icon;
          return (
            <Button
              key={index}
              variant="ghost"
              size="sm"
              onClick={item.action}
              className={cn(
                "h-8 w-8 p-0 hover:bg-gray-800",
                item.isActive() && 'bg-gray-800 text-white'
              )}
              title={item.title}
            >
              <Icon className="h-4 w-4" />
            </Button>
          );
        }
        
        return null;
      })}
    </BubbleMenu>
  )
} 