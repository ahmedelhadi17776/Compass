import { Handle, Position, NodeResizer } from '@xyflow/react';
import { useState, useCallback } from 'react';

interface CustomResizerNodeProps {
  id: string;
  data: {
    label: string;
    content?: string;
  };
  selected?: boolean;
  isConnectable?: boolean;
  updateNodeLabel: (id: string, label: string) => void;
}

const CustomResizerNode: React.FC<CustomResizerNodeProps> = ({ 
  id, 
  data, 
  selected, 
  isConnectable = true, 
  updateNodeLabel 
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [labelValue, setLabelValue] = useState(data.label);
  const [nodeDimensions, setNodeDimensions] = useState<{
    width: number | undefined;
    height: number | undefined;
  }>({
    width: undefined,
    height: undefined,
  });

  const onDoubleClick = useCallback(() => {
    setIsEditing(true);
    setLabelValue(data.label || '');
  }, [data.label]);

  const onBlur = useCallback(() => {
    setIsEditing(false);
    if (labelValue !== data.label) {
      updateNodeLabel(id, labelValue);
    }
  }, [id, labelValue, data.label, updateNodeLabel]);

  const onChange = useCallback((evt: React.ChangeEvent<HTMLInputElement>) => {
    setLabelValue(evt.target.value);
  }, []);

  const onKeyDown = useCallback((evt: React.KeyboardEvent<HTMLInputElement>) => {
    if (evt.key === 'Enter') {
      evt.preventDefault();
      (evt.target as HTMLInputElement).blur();
    }
    if (evt.key === 'Escape') {
      setLabelValue(data.label || '');
      setIsEditing(false);
    }
  }, [data.label]);

  return (
    <div style={{ height: '100%', width: '100%' }}>
      {/* Show the NodeResizer only when the node is selected */}
      {selected && (
        <NodeResizer
          minWidth={100}
          minHeight={50}
          onResize={(event, { width, height }) => {
            setNodeDimensions({ width, height });
          }}
          isVisible={selected}
        />
      )}

      <div className="flex flex-col h-full justify-center items-center p-4">
        {isEditing ? (
          <input
            className="nodrag text-base font-medium mb-2 bg-transparent border-none outline-none focus:outline-none text-center w-full"
            value={labelValue}
            onChange={onChange}
            onBlur={onBlur}
            onKeyDown={onKeyDown}
            placeholder="Enter title..."
            autoFocus
          />
        ) : (
          <div 
            className="text-base font-medium mb-2 text-center cursor-text select-none w-full"
            onDoubleClick={onDoubleClick}
          >
            {data.label || 'Untitled Node'}
          </div>
        )}
        {data.content && (
          <div className="text-sm text-center w-full">
            {data.content}
          </div>
        )}
      </div>

      {/* Add handles to allow connections */}
      <Handle
        id="top"
        type="target"
        position={Position.Top}
        className="w-2 h-2 !bg-primary"
        isConnectable={isConnectable}
      />
      <Handle
        id="right"
        type="source"
        position={Position.Right}
        className="w-2 h-2 !bg-primary"
        isConnectable={isConnectable}
      />
      <Handle
        id="bottom"
        type="source"
        position={Position.Bottom}
        className="w-2 h-2 !bg-primary"
        isConnectable={isConnectable}
      />
      <Handle
        id="left"
        type="target"
        position={Position.Left}
        className="w-2 h-2 !bg-primary"
        isConnectable={isConnectable}
      />
    </div>
  );
};

export default CustomResizerNode; 