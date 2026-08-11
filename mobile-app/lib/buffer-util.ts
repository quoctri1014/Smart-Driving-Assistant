import * as base64js from 'base64-js';

export function base64ToArrayBuffer(base64: string): ArrayBuffer {
  // react-native might include padding or data:image header, clean it first if needed.
  // expo-camera base64 does not include the data URI prefix if we don't ask for it, 
  // but just in case, strip it:
  let cleanBase64 = base64;
  if (base64.startsWith('data:image/jpeg;base64,')) {
    cleanBase64 = base64.replace('data:image/jpeg;base64,', '');
  }
  
  const byteArray = base64js.toByteArray(cleanBase64);
  return byteArray.buffer as ArrayBuffer;
}
