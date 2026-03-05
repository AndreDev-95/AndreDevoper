import { useEffect } from 'react';

export const usePageTitle = (pageTitle) => {
  useEffect(() => {
    const prevTitle = document.title;
    document.title = pageTitle ? `Andre Dev - ${pageTitle}` : 'Andre Dev';
    
    return () => {
      document.title = prevTitle;
    };
  }, [pageTitle]);
};

export default usePageTitle;
