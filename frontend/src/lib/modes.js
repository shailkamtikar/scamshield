export const MODES = {
  TEXT: "text",
  SMS_IMAGE: "sms_image",
  QR_CODE: "qr_code",
};

export const MODE_CONFIG = {
  [MODES.TEXT]: {
    label: "SMS / Text",
    icon: "sms",
    loadingHeadline: "Investigating suspicious content…",
    firstStage: "Extracting content",
  },
  [MODES.SMS_IMAGE]: {
    label: "SMS Image",
    icon: "image",
    loadingHeadline: "Investigating suspicious screenshot…",
    firstStage: "Running OCR on screenshot",
  },
  [MODES.QR_CODE]: {
    label: "QR Code",
    icon: "qr_code_2",
    loadingHeadline: "Investigating QR code…",
    firstStage: "Decoding QR code",
  },
};
