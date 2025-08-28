const path = require('path');

module.exports = [
  // Main process
  {
    entry: './src/main/main.ts',
    target: 'electron-main',
    module: {
      rules: [
        {
          test: /\.tsx?$/,
          use: 'ts-loader',
          exclude: /node_modules/,
        },
      ],
    },
    resolve: {
      extensions: ['.tsx', '.ts', '.js'],
    },
    output: {
      filename: 'main.js',
      path: path.resolve(__dirname, 'dist/main'),
    },
    node: {
      __dirname: false,
      __filename: false,
    },
  },
  // Preload process
  {
    entry: './src/main/preload.ts',
    target: 'electron-preload',
    module: {
      rules: [
        {
          test: /\.tsx?$/,
          use: 'ts-loader',
          exclude: /node_modules/,
        },
      ],
    },
    resolve: {
      extensions: ['.tsx', '.ts', '.js'],
    },
    output: {
      filename: 'preload.js',
      path: path.resolve(__dirname, 'dist/main'),
    },
    node: {
      __dirname: false,
      __filename: false,
    },
  }
];