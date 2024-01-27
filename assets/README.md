# Compilazione di Sass

La cartella  `./bootstrap` include i file scss di Bootstrap, clonati dalla repository di [GitHub](https://github.com/twbs/bootstrap/tree/main/scss) del framework.  
Qualora si desiderasse ricompilare i file è possibile farlo seguendo i seguenti passaggi:

1. Installare il compilatore Sass tramite un package manager come NPM, Chocolatey o Homebrew   
   `npm install -g sass`
2. Eseguire il compilatore, indicando come destinazione la cartella `../static`. I file risultanti dalla compilazione saranno così esposti da Flask.   
   `sass ./assets/style.scss ./static/style.css`