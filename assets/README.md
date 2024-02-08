# Compilazione di Sass

La cartella  `./bootstrap` include i file scss di Bootstrap, clonati dalla repository di [GitHub](https://github.com/twbs/bootstrap/releases/tag/v5.3.2) del framework. E' stata installata la versione 5.3.2, la più recente.   
Qualora si desiderasse ricompilare i file è possibile farlo seguendo i seguenti passaggi:

1. Installare il compilatore Sass tramite un package manager come NPM, Chocolatey o Homebrew   
   `npm install -g sass`
2. Eseguire il compilatore, indicando come destinazione la cartella `../static`. I file risultanti dalla compilazione saranno così esposti da Flask.   
   `sass ./assets/style.scss ./static/style.css`