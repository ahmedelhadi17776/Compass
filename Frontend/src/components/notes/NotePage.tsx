import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Link as LinkIcon, Share2, Star, Trash2, Tag as TagIcon } from 'lucide-react'
import TiptapEditor from './TiptapEditor'
import { z } from 'zod'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"

const titleSchema = z.string()
  .min(1, "Title is required")
  .max(200, "Title cannot be more than 200 characters")

interface Entity {
  type: 'idea' | 'tasks' | 'person' | 'todos'
  refId: string
}

interface Permission {
  userId: string
  level: 'view' | 'edit' | 'comment'
}

interface NotePageProps {
  id?: string
  userId: string
  title: string
  content: string
  linksOut?: string[]
  linksIn?: string[]
  entities?: Entity[]
  tags?: string[]
  isDeleted?: boolean
  favorited?: boolean
  icon?: string
  sharedWith?: string[]
  permissions?: Permission[]
  onSave?: (note: Partial<NotePageProps>) => void
  onDelete?: () => void
}

export default function NotePage({
  id,
  userId,
  title: initialTitle,
  content: initialContent,
  linksOut = [],
  linksIn = [],
  entities = [],
  tags = [],
  isDeleted = false,
  favorited = false,
  icon,
  sharedWith = [],
  onSave,
  onDelete
}: NotePageProps) {
  const [title, setTitle] = useState(initialTitle)
  const [content, setContent] = useState(initialContent)
  const [isFavorited, setIsFavorited] = useState(favorited)
  const [newTag, setNewTag] = useState('')
  const [localTags, setLocalTags] = useState(tags)
  const [titleError, setTitleError] = useState<string | null>(null)

  const handleTitleChange = (newTitle: string) => {
    setTitle(newTitle)
    try {
      titleSchema.parse(newTitle)
      setTitleError(null)
      onSave?.({ title: newTitle })
    } catch (error) {
      if (error instanceof z.ZodError) {
        setTitleError(error.errors[0].message)
      }
    }
  }

  const handleAddTag = (tag: string) => {
    if (tag && !localTags.includes(tag)) {
      setLocalTags([...localTags, tag])
      setNewTag('')
    }
  }

  const handleRemoveTag = (tag: string) => {
    setLocalTags(localTags.filter(t => t !== tag))
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Action buttons - vertically centered */}
      <div className="fixed right-6 top-1/2 -translate-y-1/2 flex flex-col gap-3 z-10">
        <Button
          variant="outline"
          size="icon"
          onClick={() => {
            setIsFavorited(!isFavorited)
            onSave?.({ favorited: !isFavorited })
          }}
          className={isFavorited ? 'text-yellow-500' : ''}
        >
          <Star className="h-4 w-4" />
        </Button>
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="icon">
              <Share2 className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>Copy Link</DropdownMenuItem>
            <DropdownMenuItem>Share with...</DropdownMenuItem>
            <DropdownMenuItem>Export...</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        
        {/* Add Tag Button */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="icon">
              <TagIcon className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <div className="p-2">
              <Input
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleAddTag(newTag)
                  }
                }}
                placeholder="Add tag..."
                className="text-xs text-white mb-2"
              />
              <Button 
                size="sm" 
                className="w-full"
                onClick={() => handleAddTag(newTag)}
              >
                Add
              </Button>
            </div>
          </DropdownMenuContent>
        </DropdownMenu>
        
        {onDelete && (
          <Button
            variant="outline"
            size="icon"
            onClick={onDelete}
            className="text-destructive"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        )}
      </div>
      <div className="mb-10 text-center">
        <Input
          value={title}
          onChange={(e) => handleTitleChange(e.target.value)}
          maxLength={201}
          className={cn(
            "text-4xl font-bold border-0 bg-transparent px-0 text-white text-center focus-visible:ring-0 focus-visible:ring-offset-0",
            titleError && "border-red-500"
          )}
          placeholder="Title"
        />
        {titleError && (
          <p className="text-sm text-red-500 mt-1">{titleError}</p>
        )}
      </div>

      <TiptapEditor
        content={content || "<p>Start writing...</p>"}
        onChange={(newContent) => {
          setContent(newContent)
          onSave?.({ content: newContent })
        }}
        editable={true}
        className="min-h-[500px] bg-transparent border-0"
      />

      {localTags.length > 0 && (
        <div className="mt-8 mb-12 flex flex-wrap gap-2 justify-center">
          {localTags.map((tag) => (
            <Badge 
              key={tag} 
              variant="secondary" 
              className="flex items-center gap-1 px-2 py-1"
            >
              {tag}
              <button
                onClick={() => handleRemoveTag(tag)}
                className="ml-1 hover:text-destructive"
              >
                ×
              </button>
            </Badge>
          ))}
        </div>
      )}

      {(linksIn.length > 0 || linksOut.length > 0) && (
        <div className="mt-8 pt-8 border-t">
          <h3 className="text-lg font-medium mb-4 text-white text-center">Linked Notes</h3>
          <div className="flex flex-wrap gap-2 justify-center">
            {[...linksIn, ...linksOut].map((link) => (
              <Badge key={link} variant="outline" className="flex items-center gap-1 px-3 py-1">
                <LinkIcon className="h-3 w-3" />
                {link}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  )
} 