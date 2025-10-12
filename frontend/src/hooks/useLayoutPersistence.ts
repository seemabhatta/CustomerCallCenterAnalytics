import { useState, useEffect } from 'react';

export const useLayoutPersistence = (key: string, defaultLayout: string[]) => {
  const [layout, setLayout] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem(key);
      if (stored) {
        const parsed = JSON.parse(stored);
        // Validate that stored layout contains all required items
        if (Array.isArray(parsed) && parsed.length === defaultLayout.length) {
          const hasAllItems = defaultLayout.every(item => parsed.includes(item));
          if (hasAllItems) return parsed;
        }
      }
    } catch (error) {
      console.warn('Failed to load layout from localStorage:', error);
    }
    return defaultLayout;
  });

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(layout));
    } catch (error) {
      console.warn('Failed to save layout to localStorage:', error);
    }
  }, [key, layout]);

  const resetLayout = () => {
    setLayout(defaultLayout);
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.warn('Failed to remove layout from localStorage:', error);
    }
  };

  return { layout, setLayout, resetLayout };
};
