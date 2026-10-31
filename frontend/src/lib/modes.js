export const MODES = { TEXT: "text", IMAGE: "image", QR: "qr" };

export const MODE_CONFIG = {
  [MODES.TEXT]: { label: "Paste a message", short: "Message", action: "Check this message" },
  [MODES.IMAGE]: { label: "Upload a screenshot", short: "Screenshot", action: "Check this screenshot" },
  [MODES.QR]: { label: "Scan a QR code", short: "QR code", action: "Check this QR code" },
};
