export function limparCsv(rawText) {
    const linhas = rawText.split('\n');
    return linhas.filter(linha =>
      linha.trim() &&
      !['🗑️ Remover', '{', '}', '[', 'undefined'].some(token => linha.includes(token)) &&
      linha.includes(';')
    ).join('\n');
  }
  
  export function csvToJson(csvText) {
    const lines = csvText.split('\n').filter(l => l.trim());
    const headers = lines[0].split(';').map(h => h.trim().replace(/(^"|"$)/g, '')).filter(h => h !== 'socios');
    const data = [];
  
    for (let i = 1; i < lines.length; i++) {
      const row = lines[i].split(';').map(c => c.trim().replace(/(^"|"$)/g, ''));
      const obj = {};
      headers.forEach((header, idx) => {
        obj[header] = row[idx] || '';
      });
      data.push(obj);
    }
  
    return data;
  }
  
  export function jsonToCsv(jsonArray) {
    if (!jsonArray.length) return "";
    const headers = Object.keys(jsonArray[0]);
    const csv = [headers.join(';')];
    jsonArray.forEach(obj => {
      csv.push(headers.map(h => `"${(obj[h] || '').replace(/"/g, '""')}"`).join(';'));
    });
    return csv.join('\n');
  }
  