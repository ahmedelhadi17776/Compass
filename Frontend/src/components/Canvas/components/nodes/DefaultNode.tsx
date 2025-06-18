import { Handle, Position } from '@xyflow/react';
import { useState, useCallback } from 'react';

interface DefaultNodeProps {
  id: string;
  data: {
    label: string;
    content?: string;
  };
  isConnectable?: boolean;
  updateNodeLabel: (id: string, label: string) => void;
}

const DefaultNode: React.FC<DefaultNodeProps> = ({ id, data, isConnectable = true, updateNodeLabel }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [labelValue, setLabelValue] = useState(data.label);

  const onDoubleClick = useCallback(() => {
    console.log('Double click triggered on node:', id)
    setIsEditing(true);
    setLabelValue(data.label || '');
  }, [data.label, id]);

  const onBlur = useCallback(() => {
    console.log('onBlur triggered, isEditing:', isEditing, 'labelValue:', labelValue, 'data.label:', data.label)
    setIsEditing(false);
    if (labelValue !== data.label) {
      console.log('Calling updateNodeLabel with:', { id, labelValue })
      updateNodeLabel(id, labelValue);
    }
  }, [id, labelValue, data.label, updateNodeLabel, isEditing]);

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

export default DefaultNode; 