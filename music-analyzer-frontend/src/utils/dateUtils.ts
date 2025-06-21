/**
 * Parses a date string that may contain microseconds (6 decimal places)
 * JavaScript Date only supports milliseconds (3 decimal places)
 * @param dateString - ISO date string potentially with microseconds
 * @returns Date object
 */
export const parseDate = (dateString: string | null | undefined): Date => {
  // Handle null/undefined cases
  if (!dateString) {
    return new Date(); // Return current date as fallback
  }
  
  // Handle empty string
  if (dateString.trim() === '') {
    return new Date();
  }
  
  try {
    // First try parsing as-is
    const date = new Date(dateString);
    
    // Check if date is valid
    if (!isNaN(date.getTime())) {
      return date;
    }
    
    // If invalid, try removing extra decimal places
    // Match pattern: YYYY-MM-DDTHH:mm:ss.SSSSSS (6 decimal places)
    // Replace with: YYYY-MM-DDTHH:mm:ss.SSS (3 decimal places)
    const normalizedDate = dateString.replace(/(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3})\d+/, '$1');
    const normalizedDateObj = new Date(normalizedDate);
    
    if (!isNaN(normalizedDateObj.getTime())) {
      return normalizedDateObj;
    }
    
    // If still invalid, return current date as fallback
    console.error('Invalid date string:', dateString);
    return new Date();
  } catch (error) {
    console.error('Error parsing date:', error, 'Date string:', dateString);
    return new Date();
  }
};