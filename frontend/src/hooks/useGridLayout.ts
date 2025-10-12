import { useState, useEffect } from 'react';

// Simple row-based layout: each card belongs to a row
export interface RowItem {
  id: string;
  row: number;
}

const createDefaultRows = (cardIds: string[], defaultRowMap?: Record<string, number>): RowItem[] => {
  return cardIds.map((id, index) => ({
    id,
    row: defaultRowMap?.[id] ?? index,
  }));
};

export const useRowLayout = (
  key: string,
  defaultCards: string[],
  defaultRowMap?: Record<string, number>,
) => {
  const [items, setItems] = useState<RowItem[]>(() => {
    try {
      const stored = localStorage.getItem(key);
      if (stored) {
        const parsed = JSON.parse(stored) as RowItem[];
        if (Array.isArray(parsed) && parsed.length === defaultCards.length) {
          const storedIds = parsed.map(item => item.id);
          const hasAllItems = defaultCards.every(id => storedIds.includes(id));
          const matchesDefaultRows = defaultRowMap
            ? parsed.every(item => {
                const desiredRow = defaultRowMap[item.id];
                return desiredRow === undefined || item.row === desiredRow;
              })
            : true;
          if (hasAllItems && matchesDefaultRows) return parsed;
        }
      }
    } catch (error) {
      console.warn('Failed to load row layout from localStorage:', error);
    }
    return createDefaultRows(defaultCards, defaultRowMap);
  });

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(items));
    } catch (error) {
      console.warn('Failed to save row layout to localStorage:', error);
    }
  }, [key, items]);

  const moveItem = (activeId: string, overId: string) => {
    setItems((currentItems) => {
      const activeIndex = currentItems.findIndex(item => item.id === activeId);
      const overIndex = currentItems.findIndex(item => item.id === overId);

      if (activeIndex === -1 || overIndex === -1) return currentItems;

      const activeItem = currentItems[activeIndex];
      const overItem = currentItems[overIndex];

      // Swap positions
      const newItems = [...currentItems];
      newItems[activeIndex] = { ...activeItem, row: overItem.row };
      newItems[overIndex] = { ...overItem, row: activeItem.row };

      return newItems;
    });
  };

  const resetLayout = () => {
    setItems(createDefaultRows(defaultCards, defaultRowMap));
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.warn('Failed to remove row layout from localStorage:', error);
    }
  };

  // Group items by row for rendering
  const getRows = () => {
    const rowMap = new Map<number, RowItem[]>();
    items.forEach(item => {
      if (!rowMap.has(item.row)) {
        rowMap.set(item.row, []);
      }
      rowMap.get(item.row)!.push(item);
    });

    // Convert to sorted array of rows
    return Array.from(rowMap.entries())
      .sort(([rowA], [rowB]) => rowA - rowB)
      .map(([_, rowItems]) => rowItems);
  };

  return { items, moveItem, resetLayout, getRows };
};
