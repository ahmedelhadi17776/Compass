import { create } from 'zustand';

type DragStore = {
  lastDroppedId: string | null;
  setLastDroppedId: (id: string | null) => void;
};

export const useDragStore = create<DragStore>((set) => ({
  lastDroppedId: null,
  setLastDroppedId: (id) => set({ lastDroppedId: id }),
}));