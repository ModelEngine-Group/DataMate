import { UploadFile } from "antd";
import jsSHA from "jssha";

const CHUNK_SIZE = 1024 * 1024 * 60;

export function sliceFile(file, chunkSize = CHUNK_SIZE): Blob[] {
  const totalSize = file.size;
  let start = 0;
  let end = start + chunkSize;
  const chunks = [];
  while (start < totalSize) {
    const blob = file.slice(start, end);
    chunks.push(blob);

    start = end;
    end = start + chunkSize;
  }
  return chunks;
}

export function calculateSHA256(file: Blob): Promise<string> {
  let count = 0;
  const hash = new jsSHA("SHA-256", "ARRAYBUFFER", { encoding: "UTF8" });
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    function readChunk(start: number, end: number) {
      const slice = file.slice(start, end);
      reader.readAsArrayBuffer(slice);
    }

    const bufferChunkSize = 1024 * 1024 * 20;

    function processChunk(offset: number) {
      const start = offset;
      const end = Math.min(start + bufferChunkSize, file.size);
      count = end;

      readChunk(start, end);
    }

    reader.onloadend = function () {
      const arraybuffer = reader.result;

      hash.update(arraybuffer);
      if (count < file.size) {
        processChunk(count);
      } else {
        resolve(hash.getHash("HEX", { outputLen: 256 }));
      }
    };

    processChunk(0);
  });
}

export function checkIsFilesExist(
  fileList: UploadFile[]
): Promise<UploadFile | null> {
  return new Promise((resolve) => {
    const loadEndFn = (file: UploadFile, reachEnd: boolean, e) => {
      const fileNotExist = !e.target.result;
      if (fileNotExist) {
        resolve(file);
      }
      if (reachEnd) {
        resolve(null);
      }
    };

    for (let i = 0; i < fileList.length; i++) {
      const { originFile: file } = fileList[i];
      const fileReader = new FileReader();
      fileReader.readAsArrayBuffer(file);
      fileReader.onloadend = (e) =>
        loadEndFn(fileList[i], i === fileList.length - 1, e);
    }
  });
}
