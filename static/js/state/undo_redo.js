import { captureState } from './capture.js';
import { applyState } from './apply.js';

let undoStack = [];
let redoStack = [];

export function pushStateToUndo() {
  undoStack.push(JSON.stringify(captureState()));
  redoStack = [];
}

export function undo() {
  if (undoStack.length > 0) {
    redoStack.push(JSON.stringify(captureState()));
    applyState(JSON.parse(undoStack.pop()));
  }
}

export function redo() {
  if (redoStack.length > 0) {
    undoStack.push(JSON.stringify(captureState()));
    applyState(JSON.parse(redoStack.pop()));
  }
}
