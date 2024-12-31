// 选择一个SVG元素并返回一个SVGElement实例
const selectSVG = id => {
  const el = document.getElementById(id);
  return new SVGElement(el);
};

// 创建一个新的SVG元素并返回一个SVGElement实例
const createSVG = type => {
  const el = document.createElementNS('http://www.w3.org/2000/svg', type);
  return new SVGElement(el);
};

// SVGElement类封装了对SVG元素的操作
class SVGElement {
  constructor(element) {
    this.element = element;
  }

  // 设置SVG元素的属性
  set(attributeName, value) {
    this.element.setAttribute(attributeName, value);
  }

  // 设置SVG元素的样式
  style(property, value) {
    this.element.style[property] = value;
  }
}

// 定义一组颜色和它们的不同色调
const colors = [
  { main: '#FBDB4A', shades: ['#FAE073', '#FCE790', '#FADD65', '#E4C650'] },
  { main: '#F3934A', shades: ['#F7B989', '#F9CDAA', '#DD8644', '#F39C59'] },
  { main: '#EB547D', shades: ['#EE7293', '#F191AB', '#D64D72', '#C04567'] },
  { main: '#9F6AA7', shades: ['#B084B6', '#C19FC7', '#916198', '#82588A'] },
  { main: '#5476B3', shades: ['#6382B9', '#829BC7', '#4D6CA3', '#3E5782'] },
  { main: '#2BB19B', shades: ['#4DBFAD', '#73CDBF', '#27A18D', '#1F8171'] },
  { main: '#70B984', shades: ['#7FBE90', '#98CBA6', '#68A87A', '#5E976E'] }
];

// 获取SVG元素、文本和输入框元素
const svg = selectSVG('svg');
const text = document.getElementById('text');
const offscreenText = document.getElementById('offscreen-text');
const input = document.getElementById('input');

// 初始化页面尺寸和其他变量
let width = window.innerWidth;
let height = window.innerHeight;
let textSize = 0;
let textCenter = 0;
const letters = [];
const prompt = ['你', '好',' ','陌', '生', '人', '欢', '迎','来','到','我','的','网','页'];
let runPrompt = true;

// 调整页面大小时调用的函数
const resizePage = () => {
  width = window.innerWidth;
  height = window.innerHeight;
  svg.set('height', height);
  svg.set('width', width);
  svg.set('viewBox', `0 0 ${width} ${height}`);
  resizeLetters();  // 调整文字尺寸
};

// 调整文字尺寸的函数
const resizeLetters = () => {
  textSize = width / (letters.length + 2);
  if (textSize > 50) textSize = 50;  // 限制字体最大尺寸
  text.style.fontSize = `${textSize}px`;
  text.style.height = `${textSize}px`;
  text.style.lineHeight = `${textSize}px`;
  offscreenText.style.fontSize = `${textSize}px`;

  const textRect = text.getBoundingClientRect();
  textCenter = textRect.top + textRect.height / 2;
  positionLetters();  // 重新定位字母位置
};

// 重新定位字母位置
const positionLetters = () => {
  letters.forEach(letter => {
    const timing = letter.shift ? 0.1 : 0;  // 控制字母移动的时间
    TweenLite.to(letter.onScreen, timing, { x: letter.offScreen.offsetLeft + 'px', ease: Power3.easeInOut });
    letter.shift = true;
  });
};

// 动画：将字母从无到有地显示
const animateLetterIn = letter => {
  const yOffset = (0.5 + Math.random() * 0.5) * textSize;
  TweenLite.fromTo(letter, 0.4, { scale: 0 }, { scale: 1, ease: Back.easeOut });
  TweenLite.fromTo(letter, 0.4, { opacity: 0 }, { opacity: 1, ease: Power3.easeOut });
  TweenLite.to(letter, 0.2, { y: -yOffset, ease: Power3.easeInOut });
  TweenLite.to(letter, 0.2, { y: 0, ease: Power3.easeInOut, delay: 0.2 });
  const rotation = -50 + Math.random() * 100;
  TweenLite.to(letter, 0.2, { rotation: rotation, ease: Power3.easeInOut });
  TweenLite.to(letter, 0.2, { rotation: 0, ease: Power3.easeInOut, delay: 0.2 });
};

// 添加装饰效果，如三角形和圆形
const addDecor = (letter, color) => {
  setTimeout(() => {
    var rect = letter.getBoundingClientRect();
    const x0 = letter.offsetLeft + letter.offsetWidth / 2;
    const y0 = textCenter - textSize * 0.5;
    const shade = color.shades[Math.floor(Math.random() * 4)];
    for (var i = 0; i < 8; i++) addTri(x0, y0, shade);
    for (var i = 0; i < 8; i++) addCirc(x0, y0);
  }, 150);
};

// 添加三角形装饰
const addTri = (x0, y0, shade) => {
  const tri = createSVG('polygon');
  const a = Math.random();
  const a2 = a + (-0.2 + Math.random() * 0.4);
  const r = textSize * 0.52;
  const r2 = r + textSize * Math.random() * 0.2;
  const x = x0 + r * Math.cos(2 * Math.PI * a);
  const y = y0 + r * Math.sin(2 * Math.PI * a);
  const x2 = x0 + r2 * Math.cos(2 * Math.PI * a2);
  const y2 = y0 + r2 * Math.sin(2 * Math.PI * a2);
  const triSize = textSize * 0.1;
  const scale = 0.3 + Math.random() * 0.7;
  const offset = triSize * scale;
  tri.set('points', `0,0 ${triSize * 2},0 ${triSize},${triSize * 2}`);
  tri.style('fill', shade);
  svg.element.appendChild(tri.element);
  TweenLite.fromTo(tri.element, 0.6, { rotation: Math.random() * 360, scale: scale, x: x - offset, y: y - offset, opacity: 1 }, { x: x2 - offset, y: y2 - offset, opacity: 0, ease: Power1.easeInOut, onComplete: () => {
    svg.element.removeChild(tri.element);
  } });
}

// 添加圆形装饰
const addCirc = (x0, y0) => {
  const circ = createSVG('circle');
  const a = Math.random();
  const r = textSize * 0.52;
  const r2 = r + textSize;
  const x = x0 + r * Math.cos(2 * Math.PI * a);
  const y = y0 + r * Math.sin(2 * Math.PI * a);
  const x2 = x0 + r2 * Math.cos(2 * Math.PI * a);
  const y2 = y0 + r2 * Math.sin(2 * Math.PI * a);
  const circSize = textSize * 0.05 * Math.random();
  circ.set('r', circSize);
  circ.style('fill', '#eee');
  svg.element.appendChild(circ.element);
  TweenLite.fromTo(circ.element, 0.6, { x: x - circSize, y: y - circSize, opacity: 1 }, { x: x2 - circSize, y: y2 - circSize, opacity: 0, ease: Power1.easeInOut, onComplete: () => {
    svg.element.removeChild(circ.element);
  } });
}

// 添加一个新的字母到文本中
const addLetter = (char, i) => {
  const letter = document.createElement('span');
  const oLetter = document.createElement('span');
  letter.innerHTML = char;
  oLetter.innerHTML = char;
  text.appendChild(letter);
  const color = colors[i % colors.length];
  letter.style.color = color.main;
  offscreenText.appendChild(oLetter);
  letters[i] = { offScreen: oLetter, onScreen: letter, char: char };
  animateLetterIn(letter);  // 动画显示字母
  addDecor(oLetter, color);  // 添加装饰
}

// 添加字母并更新文本
const addLetters = value => {
  value.forEach((char, i) => {
    if (letters[i] && letters[i].char !== char) {
      letters[i].onScreen.innerHTML = char;
      letters[i].offScreen.innerHTML = char;
      letters[i].char = char;
    }
    if (letters[i] === undefined) {
      addLetter(char, i);
    }
  });
};

// 从文本中移除字母并执行动画
const animateLetterOut = (letter, i) => {
  TweenLite.to(letter.onScreen, 0.1, { scale: 0, opacity: 0, ease: Power2.easeIn, onComplete: () => {
    console.log('removing');
    console.log(letter);
    offscreenText.removeChild(letter.offScreen);
    text.removeChild(letter.onScreen);
    positionLetters();  // 重新调整字母位置
  } });
  letters.splice(i, 1);  // 移除字母
}

// 根据输入值移除字母
const removeLetters = value => {
  for (let i = letters.length - 1; i >= 0; i--) {
    const letter = letters[i];
    if (value[i] === undefined) {
      animateLetterOut(letter, i);
    }
  }
}

// 监听输入框内容变化
const onInputChange = () => {
  const value = input.value === '' ? [] : input.value.toLowerCase().split('');
  addLetters(value);  // 添加字母
  removeLetters(value);  // 移除字母
  resizeLetters();  // 调整字母尺寸
};

// 键盘事件处理函数
const keyup = (e) => {
  if (runPrompt) {
    input.value = '';
    runPrompt = false;
  }
  onInputChange();  // 处理输入框变化
}

// 提示文本自动输入函数
const addPrompt = (i) => {
  setTimeout(() => {
    if (runPrompt && prompt[i]) {
      input.value = input.value + prompt[i];
      onInputChange();  // 更新输入框内容
      addPrompt(i + 1);  // 继续添加提示文本
    }
  }, 300);
}

// 初始化页面
resizePage();
window.addEventListener('resize', resizePage);  // 监听窗口大小变化
input.addEventListener('keyup', keyup);  // 监听键盘输入
input.focus();  // 聚焦输入框
addPrompt(0);  // 开始提示文本自动输入

document.getElementById('input').addEventListener('input', function(e) {
  const inputValue = e.target.value; // 获取输入框的值
  if (inputValue === 'HOME') { // 检查是否输入了特定文字
      window.location.href = 'D:/cyy/code/html/homepage/homepage-main/index.html' // 跳转到指定的URL
  }
});