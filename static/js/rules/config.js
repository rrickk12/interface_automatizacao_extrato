export function carregarRegrasConfig(url = '/rules') {
    return fetch(url)
      .then(response => {
        if (!response.ok) throw new Error(`Erro ao carregar ${url}: ${response.statusText}`);
        return response.json();
      });
  }
  