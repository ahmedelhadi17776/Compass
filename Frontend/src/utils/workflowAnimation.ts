import { WorkflowStep } from "@/types/workflow";

export interface StepConnectionInfo {
  rowIndex: number;
  colIndex: number;
  stepId: string;
  isCompleted: boolean;
}

export function calculateLineAnimations(
  groupedSteps: WorkflowStep[][],
  completedSteps: string[]
) {
  // Create a map of step connections
  const stepMap = new Map<string, StepConnectionInfo>();
  
  // Populate the map
  groupedSteps.forEach((row, rowIndex) => {
    row.forEach((step, colIndex) => {
      stepMap.set(step.id, {
        rowIndex,
        colIndex,
        stepId: step.id,
        isCompleted: completedSteps.includes(step.id)
      });
    });
  });
  
  // Calculate the horizontal line animations
  const horizontalLines = groupedSteps.map((row, rowIndex) => {
    const completedInRow = row.filter(step => completedSteps.includes(step.id));
    
    if (completedInRow.length === 0) return 0;
    if (completedInRow.length === row.length) return 100;
    
    const isRtl = rowIndex % 2 !== 0;
    const completedIndices = row
      .map((step, idx) => ({ step, idx }))
      .filter(({ step }) => completedSteps.includes(step.id))
      .map(({ idx }) => idx);
    
    const lastCompletedIndex = Math.max(...completedIndices);
    return (lastCompletedIndex / (row.length - 1)) * 100;
  });
  
  // Calculate the vertical line animations
  const verticalLines = groupedSteps.slice(1).map((_, rowIndex) => {
    // rowIndex here is the destination row (1-based since we sliced)
    const actualRowIndex = rowIndex + 1;
    const prevRowIndex = actualRowIndex - 1;
    
    const isPrevRowLTR = prevRowIndex % 2 === 0;
    const prevRow = groupedSteps[prevRowIndex];
    const currentRow = groupedSteps[actualRowIndex];
    
    // Connection nodes based on row direction pattern
    const prevRowNode = isPrevRowLTR
      ? prevRow[prevRow.length - 1]
      : prevRow[0];
      
    const currentRowNode = currentRow[0];
    
    if (completedSteps.includes(prevRowNode.id) && 
        completedSteps.includes(currentRowNode.id)) {
      return 100;
    } else if (completedSteps.includes(prevRowNode.id)) {
      return 50;
    }
    
    return 0;
  });
  
  // Get the connection status for the most recently completed step
  const getConnectionPath = (stepId: string): number[][] => {
    if (!stepMap.has(stepId)) return [];
    
    const { rowIndex, colIndex } = stepMap.get(stepId)!;
    const path: number[][] = [];
    
    // Add all rows up to the current one
    for (let r = 0; r <= rowIndex; r++) {
      // For each row, determine how far the highlight should go
      const rowSteps = groupedSteps[r];
      const isRtl = r % 2 !== 0;
      
      // If this is the target row, highlight up to the target column
      if (r === rowIndex) {
        path.push([r, isRtl ? rowSteps.length - 1 - colIndex : colIndex]);
      }
      // Otherwise highlight the full row if it should be highlighted
      else if (rowSteps.every(step => completedSteps.includes(step.id))) {
        path.push([r, rowSteps.length - 1]);
      }
      // Or partially highlight the row based on completed steps
      else {
        const completedInRow = rowSteps.filter(step => completedSteps.includes(step.id));
        if (completedInRow.length > 0) {
          const lastCompletedIndex = Math.max(
            ...rowSteps
              .map((step, idx) => ({ step, idx }))
              .filter(({ step }) => completedSteps.includes(step.id))
              .map(({ idx }) => idx)
          );
          path.push([r, isRtl ? rowSteps.length - 1 - lastCompletedIndex : lastCompletedIndex]);
        }
      }
    }
    
    return path;
  };
  
  return {
    horizontalLines,
    verticalLines,
    getConnectionPath
  };
} 