import { useState, useEffect } from "react";

interface Props {
  urls: string[];
  objectX?: number;
  objectY?: number;
  alt?: string;
  className?: string;
  interval?: number; // ms between slides, default 4000
  fallback?: React.ReactNode;
}

export function ImageSlideshow({
  urls,
  objectX = 50,
  objectY = 50,
  alt = "",
  className = "w-full h-full object-cover",
  interval = 4000,
  fallback,
}: Props) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (urls.length <= 1) return;
    const timer = setInterval(() => {
      setIndex((i) => (i + 1) % urls.length);
    }, interval);
    return () => clearInterval(timer);
  }, [urls.length, interval]);

  if (!urls.length) return <>{fallback}</>;

  return (
    <img
      key={urls[index]}
      src={urls[index]}
      alt={alt}
      className={className}
      style={{ objectPosition: `${objectX}% ${objectY}%` }}
    />
  );
}
