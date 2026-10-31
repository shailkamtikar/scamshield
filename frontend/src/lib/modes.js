export const MODES = { TEXT: "text", IMAGE: "image", QR: "qr" };

export const MODE_CONFIG = {
  [MODES.TEXT]: { no: "01", label: "Message", hint: "Paste an SMS, WhatsApp message or email" },
  [MODES.IMAGE]: { no: "02", label: "Screenshot", hint: "Upload a screenshot of the message" },
  [MODES.QR]: { no: "03", label: "QR code", hint: "Scan with your camera or upload an image" },
};
