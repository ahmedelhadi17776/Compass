import { useState } from 'react'
import NoteSidebar from './NoteSidebar'
import NotePage from './NotePage'
import { cn } from '@/lib/utils'

interface Note {
  id: string
  userId: string
  title: string
  content: string
  linksOut: string[]
  linksIn: string[]
  entities: {
    type: 'idea' | 'tasks' | 'person' | 'todos'
    refId: string
  }[]
  tags: string[]
  isDeleted: boolean
  favorited: boolean
  icon?: string
  sharedWith: string[]
  updatedAt: string
}

// Sample rich content note to test Tiptap features
const sampleNote: Note = {
  id: 'sample-note',
  userId: 'current-user',
  title: '📝 Welcome to Your New Note Taking App!',
  content: `
    <h1>Welcome to Your Enhanced Note Taking Experience! 🚀</h1>
    <p>This is a sample note showcasing the rich text editing capabilities of your new note-taking app. Here are some features you can try:</p>
    
    <h2>📌 Basic Formatting</h2>
    <p>You can make text <strong>bold</strong>, <em>italic</em>, or both <strong><em>bold and italic</em></strong>!</p>
    
    <h2>📋 Task Lists</h2>
    <ul data-type="taskList">
      <li data-type="taskItem" data-checked="true">Create your first note</li>
      <li data-type="taskItem" data-checked="false">Explore the formatting options</li>
      <li data-type="taskItem" data-checked="false">Share with your team</li>
    </ul>
    
    <h2>📊 Different Types of Lists</h2>
    <ul>
      <li>Bullet points for unordered items</li>
      <li>Perfect for brainstorming</li>
    </ul>
    
    <ol>
      <li>Numbered lists for steps</li>
      <li>Great for procedures</li>
    </ol>
    
    <h2>💫 Text Alignment</h2>
    <p style="text-align: center">This text is centered!</p>
    <p style="text-align: right">And this one is right-aligned.</p>
    
    <h2>🔤 Typography</h2>
    <p>Smart typography features like "quotes" and -- dashes are automatically enhanced.</p>
    
    <blockquote>
      <p>You can also create beautiful blockquotes like this one!</p>
    </blockquote>
    
    <h2>🎯 Next Steps</h2>
    <p>Try editing this note or create a new one to explore all the features. Happy note-taking! 🎉</p>
  `,
  linksOut: [],
  linksIn: [],
  entities: [],
  tags: ['welcome', 'tutorial', 'features'],
  isDeleted: false,
  favorited: true,
  sharedWith: [],
  updatedAt: new Date().toISOString()
}

export default function Notes() {
  const [notes, setNotes] = useState<Note[]>([sampleNote]) // Initialize with sample note
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>('sample-note') // Select sample note by default
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

  const selectedNote = notes.find(note => note.id === selectedNoteId)

  const handleCreateNote = () => {
    const newNote: Note = {
      id: Date.now().toString(),
      userId: 'current-user',
      title: 'Untitled Note',
      content: '<p></p>',
      linksOut: [],
      linksIn: [],
      entities: [],
      tags: [],
      isDeleted: false,
      favorited: false,
      sharedWith: [],
      updatedAt: new Date().toISOString()
    }

    setNotes(prev => [newNote, ...prev])
    setSelectedNoteId(newNote.id)
  }

  const handleSaveNote = (noteId: string, updates: Partial<Note>) => {
    setNotes(prev => prev.map(note => 
      note.id === noteId
        ? { 
            ...note, 
            ...updates, 
            updatedAt: new Date().toISOString() 
          }
        : note
    ))
  }

  const handleDeleteNote = (noteId: string) => {
    setNotes(prev => prev.filter(note => note.id !== noteId))
    setSelectedNoteId(null)
  }

  return (
    <div className="flex h-full relative overflow-hidden">
      <NoteSidebar
        notes={notes}
        onNoteSelect={setSelectedNoteId}
        onCreateNote={handleCreateNote}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      />
      
      <div className={cn(
        "flex-1 h-full overflow-hidden relative transition-all duration-300",
        isSidebarCollapsed ? "ml-0" : "ml-0"
      )}>
        <div className="h-full overflow-auto">
          {selectedNote ? (
            <NotePage
              {...selectedNote}
              onSave={(updates) => handleSaveNote(selectedNote.id, updates)}
              onDelete={() => handleDeleteNote(selectedNote.id)}
            />
          ) : (
            <div className="flex h-full items-center justify-center text-white/70">
              Select a note or create a new one
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 