var webpack = require('webpack');

module.exports = {
  context: __dirname + '/drf_auto/js',
  entry: './index.js',
  output: {
    path: __dirname + '/drf_auto/js',
    filename: 'dist.min.js'
  },
  devtool: 'source-map',
  plugins: [
    new webpack.NoErrorsPlugin()
  ],
  module: {
    loaders: [{
      test: /\.js?$/,
      exclude: /node_modules/,
      loader: 'babel',
      query: {
        presets: ['es2015', 'react']
      }
    }]
  }
};
