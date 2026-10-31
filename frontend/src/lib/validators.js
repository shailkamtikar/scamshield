const MAX_BYTES = 8 * 1024 * 1024;
const TYPES = ["image/png", "image/jpeg", "image/webp"];

/** Friendly client-side check; the server still validates the real file content. */
export function validateImage(file) {
  if (!TYPES.includes(file.type)) return "Please choose a PNG, JPEG or WEBP image.";
  if (file.size > MAX_BYTES) return "That image is larger than 8 MB. Please try a smaller one.";
  return null;
}
