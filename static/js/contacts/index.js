import { loadContacts } from './load.js';
import { saveContacts } from './save.js';
import { renderContacts } from './render.js';
import { updateContact, removeContact } from './update.js';
import { exportContacts, importContacts } from './import_export.js';
import { showAddContactForm, hideAddContactForm, setupFormListener } from './form.js';

document.addEventListener('DOMContentLoaded', () => {
  window.contatos = [];
  loadContacts();
  setupFormListener();

  const importInput = document.getElementById('import-contacts-input');
  if (importInput) {
    importInput.addEventListener('change', importContacts);
  }
});

// Exporta globalmente se necessário
export {
  showAddContactForm,
  hideAddContactForm,
  setupFormListener,
  renderContacts,
  removeContact,
  updateContact,
  exportContacts,
  importContacts,
  loadContacts,
  saveContacts
};
