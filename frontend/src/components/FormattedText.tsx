import React from 'react';

const tags: Record<string, string> = {
  '**': 'strong',
  '~~': 'del',
  '*': 'strong',
  '`': 'code',
  '_': 'em',
};

interface FormattedTextProps {
  text: string;
}

/**
 * a simple formatter to handle telegram-style markdown
 */
const FormattedText: React.FC<FormattedTextProps> = ({ text }) => {
  const result: React.ReactNode[] = [];
  let remaining = text;
  const markers = Object.keys(tags).sort((a, b) => b.length - a.length);

  while (remaining) {
    let bestIndex = -1;
    let bestMarker = '';

    for (const marker of markers) {
      const index = remaining.indexOf(marker);
      if (index !== -1 && (bestIndex === -1 || index < bestIndex)) {
        bestIndex = index;
        bestMarker = marker;
      }
    }

    if (bestIndex === -1) {
      result.push(remaining);
      break;
    }

    result.push(remaining.slice(0, bestIndex));
    const start = bestIndex + bestMarker.length;
    const end = remaining.indexOf(bestMarker, start);

    if (end === -1) {
      result.push(bestMarker);
      remaining = remaining.slice(start);
    } else {
      const Tag = tags[bestMarker];
      result.push(React.createElement(Tag, { key: result.length }, remaining.slice(start, end)));
      remaining = remaining.slice(end + bestMarker.length);
    }
  }

  return (
    <>
      {result.map((part, index) => (
        typeof part === 'string' 
          ? part.split('\n').map((line, i, arr) => (
              <React.Fragment key={`${index}-${i}`}>
                {line}
                {i < arr.length - 1 && <br />}
              </React.Fragment>
            ))
          : part
      ))}
    </>
  );
};

export default FormattedText;
