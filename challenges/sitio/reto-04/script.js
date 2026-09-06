

document.getElementById('btn-endpoint').addEventListener('click', () => {
      fetch('./flag/flag.json')
        .then(response => {
          if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('Datos recibidos');
        })
        .catch(error => {
          console.error('Error al realizar la petición:', error);
        });
    });
