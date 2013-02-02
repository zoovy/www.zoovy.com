/**
 * Adobe Edge: symbol definitions
 */
(function($, Edge, compId){
//images folder
var im='images/';

var fonts = {};


var resources = [
];
var symbols = {
"stage": {
   version: "1.0.0",
   minimumCompatibleVersion: "0.1.7",
   build: "1.0.0.185",
   baseState: "Base State",
   initialState: "Base State",
   gpuAccelerate: false,
   resizeInstances: false,
   content: {
         dom: [
         {
            id:'different_back',
            type:'image',
            rect:['0','0','960px','143px','auto','auto'],
            fill:["rgba(0,0,0,0)",im+"different_back.png",'0px','0px']
         },
         {
            id:'rec1',
            type:'image',
            rect:['0','0','960px','143px','auto','auto'],
            opacity:0,
            fill:["rgba(0,0,0,0)",im+"rec1.png",'0px','0px']
         },
         {
            id:'rec2',
            type:'image',
            rect:['0','0','960px','143px','auto','auto'],
            opacity:0,
            fill:["rgba(0,0,0,0)",im+"rec2.png",'0px','0px']
         },
         {
            id:'rec3',
            type:'image',
            rect:['0','0','960px','143px','auto','auto'],
            opacity:0,
            fill:["rgba(0,0,0,0)",im+"rec3.png",'0px','0px']
         },
         {
            id:'rec4',
            type:'image',
            rect:['0','0','960px','143px','auto','auto'],
            opacity:0,
            fill:["rgba(0,0,0,0)",im+"rec4.png",'0px','0px']
         },
         {
            id:'rec5',
            type:'image',
            rect:['0','0','960px','143px','auto','auto'],
            opacity:0,
            fill:["rgba(0,0,0,0)",im+"rec5.png",'0px','0px']
         },
         {
            id:'rec6',
            type:'image',
            rect:['0','0','960px','143px','auto','auto'],
            opacity:0,
            fill:["rgba(0,0,0,0)",im+"rec6.png",'0px','0px']
         },
         {
            id:'rec7',
            type:'image',
            rect:['0','0','960px','143px','auto','auto'],
            opacity:0,
            fill:["rgba(0,0,0,0)",im+"rec7.png",'0px','0px']
         },
         {
            id:'rec8',
            type:'image',
            rect:['0','0','960px','143px','auto','auto'],
            opacity:0,
            fill:["rgba(0,0,0,0)",im+"rec8.png",'0px','0px']
         },
         {
            id:'rec9',
            type:'image',
            rect:['0','0','960px','143px','auto','auto'],
            opacity:0,
            fill:["rgba(0,0,0,0)",im+"rec9.png",'0px','0px']
         },
         {
            id:'rec10',
            type:'image',
            rect:['0','0','960px','143px','auto','auto'],
            opacity:0,
            fill:["rgba(0,0,0,0)",im+"rec10.png",'0px','0px']
         },
         {
            id:'rec11',
            type:'image',
            rect:['0','0','960px','143px','auto','auto'],
            opacity:0,
            fill:["rgba(0,0,0,0)",im+"rec11.png",'0px','0px']
         },
         {
            id:'rec12',
            type:'image',
            rect:['0','0','960px','143px','auto','auto'],
            opacity:0,
            fill:["rgba(0,0,0,0)",im+"rec12.png",'0px','0px']
         }],
         symbolInstances: [

         ]
      },
   states: {
      "Base State": {
         "${_rec10}": [
            ["style", "opacity", '0']
         ],
         "${_rec11}": [
            ["style", "opacity", '0']
         ],
         "${_rec3}": [
            ["style", "opacity", '0']
         ],
         "${_rec5}": [
            ["style", "opacity", '0']
         ],
         "${_rec4}": [
            ["style", "opacity", '0']
         ],
         "${_rec6}": [
            ["style", "opacity", '0']
         ],
         "${_rec2}": [
            ["style", "opacity", '0']
         ],
         "${_rec9}": [
            ["style", "opacity", '0']
         ],
         "${_rec1}": [
            ["style", "opacity", '0']
         ],
         "${_Stage}": [
            ["color", "background-color", 'rgba(255,255,255,1)'],
            ["style", "width", '960px'],
            ["style", "height", '143px'],
            ["style", "overflow", 'hidden']
         ],
         "${_rec7}": [
            ["style", "opacity", '0']
         ],
         "${_rec8}": [
            ["style", "opacity", '0']
         ],
         "${_rec12}": [
            ["style", "opacity", '0']
         ]
      }
   },
   timelines: {
      "Default Timeline": {
         fromState: "Base State",
         toState: "",
         duration: 11000,
         autoPlay: true,
         labels: {
            "Label 1": 0
         },
         timeline: [
            { id: "eid24", tween: [ "style", "${_rec9}", "opacity", '1', { fromValue: '0'}], position: 2443, duration: 554 },
            { id: "eid25", tween: [ "style", "${_rec9}", "opacity", '0', { fromValue: '1'}], position: 4592, duration: 515 },
            { id: "eid32", tween: [ "style", "${_rec9}", "opacity", '1', { fromValue: '0'}], position: 7181, duration: 554 },
            { id: "eid33", tween: [ "style", "${_rec9}", "opacity", '0', { fromValue: '1'}], position: 9330, duration: 515 },
            { id: "eid12", tween: [ "style", "${_rec10}", "opacity", '1', { fromValue: '0'}], position: 393, duration: 393 },
            { id: "eid13", tween: [ "style", "${_rec10}", "opacity", '0', { fromValue: '1'}], position: 1762, duration: 595 },
            { id: "eid29", tween: [ "style", "${_rec10}", "opacity", '1', { fromValue: '0'}], position: 5030, duration: 686 },
            { id: "eid28", tween: [ "style", "${_rec10}", "opacity", '0', { fromValue: '1'}], position: 6425, duration: 756 },
            { id: "eid22", tween: [ "style", "${_rec11}", "opacity", '1', { fromValue: '0'}], position: 3322, duration: 607 },
            { id: "eid23", tween: [ "style", "${_rec11}", "opacity", '0', { fromValue: '1'}], position: 5990, duration: 626 },
            { id: "eid4", tween: [ "style", "${_rec2}", "opacity", '1', { fromValue: '0'}], position: 647, duration: 1243 },
            { id: "eid7", tween: [ "style", "${_rec2}", "opacity", '0', { fromValue: '1'}], position: 3600, duration: 992 },
            { id: "eid41", tween: [ "style", "${_rec12}", "opacity", '1', { fromValue: '0'}], position: 1920, duration: 536 },
            { id: "eid40", tween: [ "style", "${_rec12}", "opacity", '0', { fromValue: '1'}], position: 3691, duration: 515 },
            { id: "eid20", tween: [ "style", "${_rec7}", "opacity", '1', { fromValue: '0'}], position: 3025, duration: 511 },
            { id: "eid21", tween: [ "style", "${_rec7}", "opacity", '0', { fromValue: '1'}], position: 4487, duration: 526 },
            { id: "eid36", tween: [ "style", "${_rec7}", "opacity", '1', { fromValue: '0'}], position: 7181, duration: 511 },
            { id: "eid37", tween: [ "style", "${_rec7}", "opacity", '0', { fromValue: '1'}], position: 8643, duration: 526 },
            { id: "eid26", tween: [ "style", "${_rec5}", "opacity", '1', { fromValue: '0'}], position: 3138, duration: 775 },
            { id: "eid27", tween: [ "style", "${_rec5}", "opacity", '0', { fromValue: '1'}], position: 6847, duration: 907 },
            { id: "eid8", tween: [ "style", "${_rec3}", "opacity", '1', { fromValue: '0'}], position: 1035, duration: 2378 },
            { id: "eid9", tween: [ "style", "${_rec3}", "opacity", '0', { fromValue: '1'}], position: 3413, duration: 754 },
            { id: "eid10", tween: [ "style", "${_rec4}", "opacity", '1', { fromValue: '0'}], position: 2224, duration: 773 },
            { id: "eid11", tween: [ "style", "${_rec4}", "opacity", '0', { fromValue: '1'}], position: 5107, duration: 609 },
            { id: "eid18", tween: [ "style", "${_rec6}", "opacity", '1', { fromValue: '0'}], position: 4487, duration: 775 },
            { id: "eid19", tween: [ "style", "${_rec6}", "opacity", '0', { fromValue: '1'}], position: 8195, duration: 907 },
            { id: "eid14", tween: [ "style", "${_rec8}", "opacity", '1', { fromValue: '0'}], position: 1036, duration: 536 },
            { id: "eid15", tween: [ "style", "${_rec8}", "opacity", '0', { fromValue: '1'}], position: 2807, duration: 515 },
            { id: "eid39", tween: [ "style", "${_rec8}", "opacity", '1', { fromValue: '0'}], position: 5261, duration: 536 },
            { id: "eid38", tween: [ "style", "${_rec8}", "opacity", '0', { fromValue: '1'}], position: 7032, duration: 515 },
            { id: "eid34", tween: [ "style", "${_rec8}", "opacity", '1', { fromValue: '0'}], position: 9102, duration: 536 },
            { id: "eid35", tween: [ "style", "${_rec8}", "opacity", '0', { fromValue: '1'}], position: 10485, duration: 515 },
            { id: "eid1", tween: [ "style", "${_rec1}", "opacity", '1', { fromValue: '0'}], position: 0, duration: 786 },
            { id: "eid3", tween: [ "style", "${_rec1}", "opacity", '0', { fromValue: '1'}], position: 1309, duration: 1834 }         ]
      }
   }
}
};


Edge.registerCompositionDefn(compId, symbols, fonts, resources);

/**
 * Adobe Edge DOM Ready Event Handler
 */
$(window).ready(function() {
     Edge.launchComposition(compId);
});
})(jQuery, AdobeEdge, "EDGE-1205631013");
