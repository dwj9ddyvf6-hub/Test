// Exact supported surface of node:crypto used by the original Aperture core.
// Deliberately not a general crypto polyfill.
import { sha256 } from '@noble/hashes/sha2.js';
import { bytesToHex, utf8ToBytes } from '@noble/hashes/utils.js';
export function createHash(algorithm) {
  if (algorithm !== 'sha256') throw new Error('Unsupported hash algorithm');
  const hash = sha256.create();
  let finalized = false;
  return {
    update(value) {
      if (finalized) throw new Error('Digest already called');
      if (typeof value !== 'string') throw new Error('Aperture hash shim accepts UTF-8 strings only');
      hash.update(utf8ToBytes(value));
      return this;
    },
    digest(encoding) {
      if (finalized) throw new Error('Digest already called');
      if (encoding !== 'hex') throw new Error('Aperture hash shim supports hex digest only');
      finalized = true;
      return bytesToHex(hash.digest());
    },
  };
}
