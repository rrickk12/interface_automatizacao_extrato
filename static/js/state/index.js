export { captureState } from './capture.js';
export { applyState } from './apply.js';
export {
  saveStateToServer,
  loadStateFromServer,
  cleanStateOnServer
} from './server.js';
export {
  pushStateToUndo,
  undo,
  redo
} from './undo_redo.js';
export { importStateFromFile } from './import_file.js'; // ✅ aqui
