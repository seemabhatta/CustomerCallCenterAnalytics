import { ReactNode, CSSProperties } from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical } from 'lucide-react';
import { Card } from '@/components/ui/card';

interface DraggableCardProps {
  id: string;
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
}

export const DraggableCard = ({ id, children, className, style: customStyle }: DraggableCardProps) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    ...customStyle,
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} className={className}>
      <Card className="relative">
        <div
          {...attributes}
          {...listeners}
          className="absolute right-2 top-2 cursor-grab active:cursor-grabbing rounded p-1 hover:bg-slate-100 z-10"
          title="Drag to reorder"
        >
          <GripVertical className="h-4 w-4 text-slate-400" />
        </div>
        {children}
      </Card>
    </div>
  );
};

export default DraggableCard;
