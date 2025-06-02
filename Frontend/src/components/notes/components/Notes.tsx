import { useState, useEffect, useCallback } from 'react'
import NoteSidebar from './NoteSidebar'
import NotePage from './NotePage'
import { cn } from '@/lib/utils'
import { useNotes } from '@/components/notes/hooks'
import { Note } from '@/components/notes/types'

export default function Notes() {
  const { 
    notes, 
    loading, 
    error, 
    createNote, 
    updateNote, 
    deleteNote 
  } = useNotes()
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

  // Select first note by default when notes are loaded
  useEffect(() => {
    if (notes.length > 0 && !selectedNoteId) {
      setSelectedNoteId(notes[0].id)
    }
  }, [notes, selectedNoteId])

  const selectedNote = notes.find(note => note.id === selectedNoteId)
  console.log('Current selected note:', selectedNote) // Debug log

  const handleCreateNote = async () => {
    try {
      const newNote = await createNote({
        title: 'Untitled Note',
        content: '<p></p>',
        tags: [],
        favorited: false
      })
      setSelectedNoteId(newNote.id)
    } catch (error) {
      console.error('Error creating note:', error)
    }
  }

  const handleSaveNote = async (noteId: string, updates: Partial<Note>) => {
    try {
      await updateNote(noteId, updates)
    } catch (error) {
      console.error('Error updating note:', error)
    }
  }

  const handleDeleteNote = async (noteId: string) => {
    try {
      // Find the next note to select before deletion
      const currentIndex = notes.findIndex(note => note.id === noteId);
      const nextNote = notes.length > 1
        ? notes[currentIndex === notes.length - 1 ? currentIndex - 1 : currentIndex + 1]
        : null;

      // Delete the note
      await deleteNote(noteId);

      // Update selection
      if (nextNote) {
        setSelectedNoteId(nextNote.id);
      } else {
        setSelectedNoteId(null);
      }
    } catch (error) {
      console.error('Error deleting note:', error);
    }
  };

  // Update selection when notes array changes
  useEffect(() => {
    if (notes.length > 0 && !notes.some(note => note.id === selectedNoteId)) {
      setSelectedNoteId(notes[0].id);
    } else if (notes.length === 0) {
      setSelectedNoteId(null);
    }
  }, [notes, selectedNoteId]);

  const handleNoteSelect = useCallback((noteId: string) => {
    if (noteId !== selectedNoteId) {
      setSelectedNoteId(noteId)
    }
  }, [selectedNoteId])

  if (loading) return <div className="flex h-full items-center justify-center">Loading...</div>
  if (error) return <div className="flex h-full items-center justify-center text-red-500">Error: {error.message}</div>

  return (
    <div className="flex h-full relative overflow-hidden">
      <NoteSidebar
        notes={notes}
        selectedNoteId={selectedNoteId}
        onNoteSelect={handleNoteSelect}
        onCreateNote={handleCreateNote}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        loading={loading}
      />
      
      <div className={cn(
        "flex-1 h-full overflow-hidden relative transition-all duration-300",
        isSidebarCollapsed ? "ml-0" : "ml-0"
      )}>
        <div className="h-full overflow-auto">
          {selectedNote ? (
            <NotePage
              key={selectedNote.id} // Force re-render when note changes
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