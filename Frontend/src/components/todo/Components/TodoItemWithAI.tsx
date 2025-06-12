import React, { useState } from "react";
import { useDrop } from "react-dnd";
import { AIOptionsModal } from "@/components/chatbot/AIOptionsModal";
import { Todo } from "@/components/todo/types-todo";

export const TodoItemWithAI: React.FC<{
  todo: Todo;
  children: React.ReactNode;
}> = ({ todo, children }) => {
  const [showModal, setShowModal] = useState(false);

  const [{ isOver }, drop] = useDrop(() => ({
    accept: "AI_ASSISTANT",
    drop: () => {
      // When dropped, show the AI options modal
      setShowModal(true);
      return { type: "TODO", id: todo.id };
    },
    collect: (monitor) => ({
      isOver: !!monitor.isOver(),
    }),
  }));

  return (
    <div
      ref={drop}
      className={`relative ${
        isOver ? "ring-2 ring-primary ring-opacity-50" : ""
      }`}
    >
      {children}
      {showModal && (
        <AIOptionsModal
          targetType="todo"
          targetId={todo.id}
          targetData={todo}
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  );
};
