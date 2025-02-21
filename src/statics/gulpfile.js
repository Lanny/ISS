var gulp = require('gulp');
var flatten = require('gulp-flatten');
var less = require('gulp-less');
var sourcemaps = require('gulp-sourcemaps');
var path = require('path');
var argv = require('yargs').argv;
var minifyCSS = require('gulp-minify-css');
var requirejsOptimize = require('gulp-requirejs-optimize');
var concat = require('gulp-concat');
var svg = require('gulp-svg-inline-css');
var clean = require('gulp-clean');
var autoprefixer = require('gulp-autoprefixer');
var execSync = require('child_process').execSync;

var staticDir = argv.outDir || '../ISS/static',
  jsDir = path.join(staticDir, '/js'),
  cssDir = path.join(staticDir, '/css'),
  gifDir = path.join(staticDir, '/img/gif'),
  jpgDir = path.join(staticDir, '/img/jpg'),
  optimizeModules = [
    'thread.js',
    'editor-bootstrap.js',
    'auto-suggest-bootstrap.js',
    'base.js'
  ];

gulp.task('clean', function() {
  return gulp.src([ gifDir, cssDir, jsDir, jpgDir ], { allowEmpty: true })
    .pipe(clean({read: false, force: true}));
});
 
gulp.task('icons', function() {
  return gulp.src('src/assets/svg/*.svg')
    .pipe(svg({
      className: '.icn-%s()'
    }))
    .pipe(concat('icons.less'))
    .pipe(gulp.dest('src/base'));
});

gulp.task('smilies', function() {
  return gulp.src('src/assets/gif/*')
    .pipe(gulp.dest(gifDir));
});

gulp.task('jpgs', function() {
  return gulp.src('src/assets/jpg/*')
    .pipe(gulp.dest(jpgDir));
});

gulp.task('less', gulp.series('icons', function() {
  var lessStream = less({
      paths: [ path.join(__dirname, 'less') ]
    }).on('error', function(err) {
      console.error(err);
      this.emit('end');
    });

  var stream = gulp.src('./src/themes/*.less');

  stream = argv.optimizeAssets ? stream : stream.pipe(sourcemaps.init());
  stream = stream.pipe(lessStream);
  stream = argv.optimizeAssets ? stream : stream.pipe(sourcemaps.write());
  stream = stream.pipe(flatten());
  stream = stream.pipe(autoprefixer());
  stream = argv.optimizeAssets ? stream.pipe(minifyCSS()) : stream;
  stream = stream.pipe(gulp.dest(cssDir));

  return stream;
}));

gulp.task('javascript', function() {
  return gulp.src('./src/**/*.js')
    .pipe(flatten())
    .pipe(gulp.dest(jsDir));
});

gulp.task('optimize-js', gulp.series('javascript', function() {
  var optPaths = optimizeModules.map(function(moduleName) {
    return path.join(jsDir, moduleName);
  });

  return gulp.src(optPaths)
    .pipe(requirejsOptimize({ paths: { 'jquery': 'empty:' } }))
    .pipe(flatten())
    .pipe(gulp.dest(jsDir));
}));

var generateTasks = ['less', 'smilies', 'jpgs'];
generateTasks.push(argv.optimizeAssets ? 'optimize-js' : 'javascript');
gulp.task('generate', gulp.parallel(generateTasks));

gulp.task('watch', gulp.series('generate', function() {
  return Promise.all([
    gulp.watch([ './src/assets/svg/*.svg' ], gulp.series('icons')),
    gulp.watch([ './src/assets/gif/*' ], gulp.series('smilies')),
    gulp.watch([ './src/assets/jpg/*' ], gulp.series('jpgs')),
    gulp.watch([ './src/**/*.less', '!./src/base/icons.less' ], gulp.series('less')),
    gulp.watch([ './src/**/*.js' ], gulp.series('javascript')),
  ]);
}));
