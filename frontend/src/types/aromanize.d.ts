declare module 'aromanize' {
  interface Aromanize {
    romanize(text: string): string;
  }

  const aromanize: Aromanize;
  export default aromanize;
}

declare module 'aromanize/base' {
  interface Aromanize {
    romanize(text: string): string;
  }

  const aromanize: Aromanize;
  export = aromanize;
}
