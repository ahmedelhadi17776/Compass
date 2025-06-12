import React from "react";
import { useDrag } from "react-dnd";
import ChatbotIcon from "@/components/Chatbot/ChatbotIcon";

interface DragItem {
  type: string;
}

export const DraggableAIAssistant: React.FC = () => {
  const [{ isDragging }, drag] = useDrag<
    DragItem,
    unknown,
    { isDragging: boolean }
  >(() => ({
    type: "AI_ASSISTANT",
    item: { type: "AI_ASSISTANT" },
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging(),
    }),
    end: (item, monitor) => {
      // Handle the end of drag operation
      const didDrop = monitor.didDrop();
      if (!didDrop) {
        // The item was not dropped on a valid target
        console.log("AI Assistant was not dropped on a valid target");
      }
    },
  }));

  return (
    <div
      ref={drag}
      style={{
        opacity: isDragging ? 0.5 : 1,
        cursor: "grab",
        position: "fixed",
        bottom: "20px",
        right: "20px",
        zIndex: 1000,
      }}
      role="button"
      aria-label="Drag AI Assistant to items for help"
      tabIndex={0}
    >
      <ChatbotIcon toggleChat={() => {}} isChatOpen={false} />
    </div>
  );
};

export default DraggableAIAssistant;
