import { useState, useEffect } from 'react';

export interface GridItem {
  id: string;
  row: number;
  col: number;
}

const createDefaultGrid = (cardIds: string[], maxCols: number): GridItem[] => {
  return cardIds.map((id, index) => ({
    id,
    row: Math.floor(index / maxCols),
    col: index % maxCols,
  }));
};

export const useGridLayout = (key: string, defaultCards: string[], maxCols: number = 3) => {
  const [items, setItems] = useState<GridItem[]>(() => {
    try {
      const stored = localStorage.getItem(key);
      if (stored) {
        const parsed = JSON.parse(stored) as GridItem[];
        // Validate that stored layout contains all required items
        if (Array.isArray(parsed) && parsed.length === defaultCards.length) {
          const storedIds = parsed.map(item => item.id);
          const hasAllItems = defaultCards.every(id => storedIds.includes(id));
          if (hasAllItems) return parsed;
        }
      }
    } catch (error) {
      console.warn('Failed to load grid layout from localStorage:', error);
    }
    return createDefaultGrid(defaultCards, maxCols);
  });

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(items));
    } catch (error) {
      console.warn('Failed to save grid layout to localStorage:', error);
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
      newItems[activeIndex] = { ...activeItem, row: overItem.row, col: overItem.col };
      newItems[overIndex] = { ...overItem, row: activeItem.row, col: activeItem.col };

      return newItems;
    });
  };

  const resetLayout = () => {
    setItems(createDefaultGrid(defaultCards, maxCols));
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.warn('Failed to remove grid layout from localStorage:', error);
    }
  };

  // Group items by row for rendering
  const getRowGroups = () => {
    const rowMap = new Map<number, GridItem[]>();
    items.forEach(item => {
      if (!rowMap.has(item.row)) {
        rowMap.set(item.row, []);
      }
      rowMap.get(item.row)!.push(item);
    });

    // Sort items within each row by column
    rowMap.forEach((rowItems) => {
      rowItems.sort((a, b) => a.col - b.col);
    });

    // Convert to sorted array of rows
    return Array.from(rowMap.entries())
      .sort(([rowA], [rowB]) => rowA - rowB)
      .map(([_, rowItems]) => rowItems);
  };

  return { items, moveItem, resetLayout, setItems, getRowGroups, maxCols };
};
