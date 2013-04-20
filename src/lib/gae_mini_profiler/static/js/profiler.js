
var GaeMiniProfiler = {

    // Profiler modes match gae_mini_profiler.profiler.Mode's enum.
    // TODO(kamens): switch this from an enum to a more sensible bitmask or
    // other alternative that supports multiple settings without an exploding
    // number of enums.
    modes: {
               SIMPLE: "simple",
               CPU_INSTRUMENTED: "instrumented",
               CPU_SAMPLING: "sampling",
               RPC_ONLY: "rpc",
               RPC_AND_CPU_INSTRUMENTED: "rpc_instrumented",
               RPC_AND_CPU_SAMPLING: "rpc_sampling"
    },

    init: function(requestId, fShowImmediately) {
        // Fetch profile results for any ajax calls
        // (see http://code.google.com/p/mvc-mini-profiler/source/browse/MvcMiniProfiler/UI/Includes.js)
        $(document).ajaxComplete(function (e, xhr, settings) {
            if (xhr) {
                var requestId = xhr.getResponseHeader('X-MiniProfiler-Id');
                if (requestId) {
                    var queryString = xhr.getResponseHeader('X-MiniProfiler-QS');
                    GaeMiniProfiler.fetch(requestId, queryString);
                }
            }
        });

        GaeMiniProfiler.fetch(requestId, window.location.search, fShowImmediately);
    },

    /**
     * Return the profiler mode being requested by the current browser cookie.
     */
    getCookieMode: function() {
        var mode = $.cookiePlugin("g-m-p-mode");

        // Default to RPC + Instrumented
        var valid = false;
        for (var key in this.modes) {
            if (mode == this.modes[key]) {
                valid = true;
                break;
            }
        }
        if (!valid) {
            mode = this.modes.RPC_AND_CPU_INSTRUMENTED;
        }

        return mode;
    },

    /**
     * Set browser cookie for current profiler mode according to radio inputs.
     */
    setCookieMode: function(elLink) {
        // Get current state of RPC/CPU profiler settings according to radios
        var jel = $(elLink).closest(".g-m-p").find(".settings"),
            rpcValue = jel.find("input:radio[name=rpc]:checked").val(),
            cpuValue = jel.find("input:radio[name=cpu]:checked").val();

        // Convert to format matching this.modes values.
        var mode = "simple";
        if (rpcValue && cpuValue) {
            mode = rpcValue + "_" + cpuValue;
        }
        else {
            mode = rpcValue || cpuValue || "simple";
        }

        // Set mode cookie for profiler to detect on next request
        $.cookiePlugin("g-m-p-mode", mode, {path: '/', expires: 365});
    },

    /**
     * True if profiler mode has enabled RPC profiling
     */
    isRpcEnabled: function(mode) {
        return (mode == this.modes.RPC_ONLY ||
                mode == this.modes.RPC_AND_CPU_INSTRUMENTED ||
                mode == this.modes.RPC_AND_CPU_SAMPLING);
    },

    /**
     * True if profiler mode has enabled CPU instrumentation
     */
    isInstrumentedEnabled: function(mode) {
        return (mode == this.modes.CPU_INSTRUMENTED ||
                mode == this.modes.RPC_AND_CPU_INSTRUMENTED);
    },

    /**
     * True if profiler mode has enabled CPU sampling
     */
    isSamplingEnabled: function(mode) {
        return (mode == this.modes.CPU_SAMPLING ||
                mode == this.modes.RPC_AND_CPU_SAMPLING);
    },

    /**
     * True if either CPU instrumentation or CPU sampling is enabled
     */
    isCpuEnabled: function(mode) {
        return (GaeMiniProfiler.isInstrumentedEnabled(mode) ||
                GaeMiniProfiler.isSamplingEnabled(mode));
    },

    appendRedirectIds: function(requestId, queryString) {
        if (queryString) {
            var re = /mp-r-id=([^&]+)/;
            var matches = re.exec(queryString);
            if (matches && matches.length) {
                var sRedirectIds = matches[1];
                var list = sRedirectIds.split(",");
                list[list.length] = requestId;
                return list;
            }
        }

        return [requestId];
    },

    fetch: function(requestId, queryString, fShowImmediately) {
        var requestIds = this.appendRedirectIds(requestId, queryString);

        $.get(
                "/gae_mini_profiler/request",
                { "request_ids": requestIds.join(",") },
                function(data) {
                    GaeMiniProfilerTemplate.init(function() { GaeMiniProfiler.finishFetch(data, fShowImmediately); });
                },
                "json"
        );
    },

    finishFetch: function(data, fShowImmediately) {
        if (!data || !data.length) return;

        for (var ix = 0; ix < data.length; ix++) {

            var jCorner = this.renderCorner(data[ix]);

            if (!jCorner.data("attached")) {
                $('body')
                    .append(jCorner)
                    .click(function(e) { return GaeMiniProfiler.collapse(e); });
                jCorner
                    .data("attached", true);
            }

            if (fShowImmediately)
                jCorner.find(".entry").first().click();

        }
    },

    /**
     * Fetch the RequestLog data (pending_ms and loading_request) from App
     * Engine's logservice API.
     */
    fetchRequestLog: function(data, attempts) {

        // We're willing to ask the logservice API for its RequestLog data more
        // than once, because it may take App Engine a while to flush its logs.
        if (!attempts) {
            attempts = 0;
        }
        
        // We only try to get the request log three times.
        if (attempts > 2) {
            $(".g-m-p .request-log-" + data.logging_request_id)
                .html("Request log data not found.");
            return;
        }

        $.get(
            "/gae_mini_profiler/request/log",
            {
                "request_id": data.request_id,
                "logging_request_id": data.logging_request_id
            },
            function(requestLogData) {

                if (!requestLogData) {
                    // The request log may not be available just yet, because
                    // App Engine may still be writing its logs. We'll wait a 
                    // sec and try up to three times.
                    setTimeout(function() {
                        GaeMiniProfiler.fetchRequestLog(data, attempts + 1);
                    }, 1000);
                    return;
                }

                requestLogData.request_id = data.request_id;
                GaeMiniProfiler.finishFetchRequestLog(requestLogData);
            }
        );
    },

    /**
     * Render the RequestLog information (pending_ms and loading_request).
     */
    finishFetchRequestLog: function(requestLogData) {
        $(".g-m-p .request-log-" + requestLogData.logging_request_id)
            .empty()
            .append(
                $("#profilerRequestLogTemplate").tmplPlugin(
                    requestLogData));
    },

    collapse: function(e) {
        if ($(".g-m-p").is(":visible")) {
            $(".g-m-p").slideUp("fast");
            $(".g-m-p-corner").slideDown("fast")
                .find(".expanded").removeClass("expanded");
            return false;
        }

        return true;
    },

    expand: function(elEntry, data) {
        var jPopup = $(".g-m-p");

        if (jPopup.length)
            jPopup.remove();
        else
            $(document).keyup(function(e) { if (e.which == 27) GaeMiniProfiler.collapse() });

        jPopup = this.renderPopup(data);
        $('body').append(jPopup);

        var jCorner = $(".g-m-p-corner");
        jCorner.find(".expanded").removeClass("expanded");
        $(elEntry).addClass("expanded");

        jPopup
            .find(".profile-link")
                .click(function() { GaeMiniProfiler.toggleSection(this, ".profiler-details"); return false; }).end()
            .find(".rpc-link")
                .click(function() { GaeMiniProfiler.toggleSection(this, ".rpc-details"); return false; }).end()
            .find(".logs-link")
                .click(function() { GaeMiniProfiler.toggleSection(this, ".logs-details"); return false; }).end()
            .find(".callers-link")
                .click(function() { $(this).parents("td").find(".callers").slideToggle("fast"); return false; }).end()
            .find(".request-log-link")
                .click(function() { GaeMiniProfiler.showRequestLog(this); return false; }).end()
            .find(".settings-link")
                .click(function() { GaeMiniProfiler.toggleSettings(this); return false; }).end()
            .find(".settings input")
                .change(function() { GaeMiniProfiler.setCookieMode(this); return false; }).end()
            .click(function(e) { e.stopPropagation(); })
            .css("left", jCorner.offset().left + jCorner.width() + 18)
            .slideDown("fast");

        var toggleLogRows = function(level) {
            var names = {10:'Debug', 20:'Info', 30:'Warning', 40:'Error', 50:'Critical'};
            $('#slider .minlevel-text').text(names[level]);
            $('#slider .loglevel').attr('class', 'loglevel ll'+level);
            for (var i = 10; i<=50; i += 10) {
                var rows = $('tr.ll'+i);
                if (i<level)
                    rows.hide();
                else
                    rows.show();
            }
        };

        var initLevel = 10;

        if ($('#slider .control').slider) {
            initLevel = 30;
            $('#slider .control').slider({
                value: initLevel,
                min: 10,
                max: 50,
                step: 10,
                range: 'min',
                slide: function( event, ui ) {
                    toggleLogRows(ui.value);
                }
            });
        }

        toggleLogRows(initLevel);

        // Once a mini profiler entry is expanded, ask App Engine for its
        // additional request log information.
        // We wait to do this until a profiler entry is expanded because:
        //  A) RequestLogs aren't available *immediately* after a request
        //  finishes, so waiting until the profiler user shows interest in a
        //  request makes sense.
        //  B) Most profiler users won't need this data, so we don't want to
        //  use the logservice API unnecessarily.
        this.fetchRequestLog(data);
    },

    /**
     * Replace the "Show more request info" link with App Engine's RequestLog
     * data (pending_ms and loading_request), which will have been retrieved as
     * soon as the mini profiler tab was expanded.
     */
    showRequestLog: function(elLink) {

        $(elLink).closest(".g-m-p")
            .find(".request-log-link")
                .css("display", "none")
                .end()
            .find(".request-log")
                .show("fast")
                .end();

    },

    toggleSettings: function(elLink) {
        var mode = this.getCookieMode();

        var cpuSelector = "#cpu_disabled";
        if (this.isInstrumentedEnabled(mode)) {
            cpuSelector = "#cpu_instrumented";
        }
        else if (this.isSamplingEnabled(mode)) {
            cpuSelector = "#cpu_sampling";
        }

        var rpcSelector = "#rpc_disabled";
        if (this.isRpcEnabled(mode)) {
            rpcSelector = "#rpc_enabled";
        }
        
        $(elLink).closest(".g-m-p").find(".settings")
            .find(cpuSelector)
                .attr("checked", "checked")
                .end()
            .find(rpcSelector)
                .attr("checked", "checked")
                .end()
        .slideToggle("fast");
    },

    toggleSection: function(elLink, selector) {

        var fWasVisible = $(".g-m-p " + selector).is(":visible");

        $(".g-m-p .expand").removeClass("expanded");
        $(".g-m-p .details:visible").slideUp(50)

        if (!fWasVisible) {
            $(elLink).parents(".expand").addClass("expanded");
            $(selector).slideDown("fast", function() {

                var jTable = $(this).find("table");

                if (jTable.length && jTable.find("tbody").length &&
                    !jTable.data("table-sorted")) {
                    jTable
                        .tablesorter()
                        .data("table-sorted", true);
                }

            });
        }
    },

    renderPopup: function(data) {
        if (data.logs) {
            var counts = {}
            $.each(data.logs, function(i, log) {
                var c = counts[log[0]] || 0;
                counts[log[0]] = c + 1;
            });
            data.log_count = counts;
        }

        return $("#profilerTemplate").tmplPlugin(data);
    },

    renderCorner: function(data) {
        if (data && data.profiler_results) {
            var jCorner = $(".g-m-p-corner");

            var fFirst = false;
            if (!jCorner.length) {
                jCorner = $("#profilerCornerTemplate").tmplPlugin();
                fFirst = true;
            }

            return jCorner.append(
                    $("#profilerCornerEntryTemplate")
                        .tmplPlugin(data)
                        .addClass(fFirst ? "" : "ajax")
                        .click(function() { GaeMiniProfiler.expand(this, data); return false; })
                    );
        }
        return null;
    }
};

var GaeMiniProfilerTemplate = {

    template: null,

    init: function(callback) {
        $.get("/gae_mini_profiler/static/js/template.tmpl", function (data) {
            if (data) {
                $('body').append(data);
                callback();
            }
        });
    }

};

/*
 * jQuery Templates Plugin 1.0.0pre
 * http://github.com/jquery/jquery-tmpl
 * Requires jQuery 1.4.2
 *
 * Copyright Software Freedom Conservancy, Inc.
 * Dual licensed under the MIT or GPL Version 2 licenses.
 * http://jquery.org/license
 */
(function(a){var r=a.fn.domManip,d="_tmplitem",q=/^[^<]*(<[\w\W]+>)[^>]*$|\{\{\! /,b={},f={},e,p={key:0,data:{}},i=0,c=0,l=[];function g(g,d,h,e){var c={data:e||(e===0||e===false)?e:d?d.data:{},_wrap:d?d._wrap:null,tmplPlugin:null,parent:d||null,nodes:[],calls:u,nest:w,wrap:x,html:v,update:t};g&&a.extend(c,g,{nodes:[],parent:d});if(h){c.tmplPlugin=h;c._ctnt=c._ctnt||c.tmplPlugin(a,c);c.key=++i;(l.length?f:b)[i]=c}return c}a.each({appendTo:"append",prependTo:"prepend",insertBefore:"before",insertAfter:"after",replaceAll:"replaceWith"},function(f,d){a.fn[f]=function(n){var g=[],i=a(n),k,h,m,l,j=this.length===1&&this[0].parentNode;e=b||{};if(j&&j.nodeType===11&&j.childNodes.length===1&&i.length===1){i[d](this[0]);g=this}else{for(h=0,m=i.length;h<m;h++){c=h;k=(h>0?this.clone(true):this).get();a(i[h])[d](k);g=g.concat(k)}c=0;g=this.pushStack(g,f,i.selector)}l=e;e=null;a.tmplPlugin.complete(l);return g}});a.fn.extend({tmplPlugin:function(d,c,b){return a.tmplPlugin(this[0],d,c,b)},tmplItem:function(){return a.tmplItem(this[0])},template:function(b){return a.template(b,this[0])},domManip:function(d,m,k){if(d[0]&&a.isArray(d[0])){var g=a.makeArray(arguments),h=d[0],j=h.length,i=0,f;while(i<j&&!(f=a.data(h[i++],"tmplItem")));if(f&&c)g[2]=function(b){a.tmplPlugin.afterManip(this,b,k)};r.apply(this,g)}else r.apply(this,arguments);c=0;!e&&a.tmplPlugin.complete(b);return this}});a.extend({tmplPlugin:function(d,h,e,c){var i,k=!c;if(k){c=p;d=a.template[d]||a.template(null,d);f={}}else if(!d){d=c.tmplPlugin;b[c.key]=c;c.nodes=[];c.wrapped&&n(c,c.wrapped);return a(j(c,null,c.tmplPlugin(a,c)))}if(!d)return[];if(typeof h==="function")h=h.call(c||{});e&&e.wrapped&&n(e,e.wrapped);i=a.isArray(h)?a.map(h,function(a){return a?g(e,c,d,a):null}):[g(e,c,d,h)];return k?a(j(c,null,i)):i},tmplItem:function(b){var c;if(b instanceof a)b=b[0];while(b&&b.nodeType===1&&!(c=a.data(b,"tmplItem"))&&(b=b.parentNode));return c||p},template:function(c,b){if(b){if(typeof b==="string")b=o(b);else if(b instanceof a)b=b[0]||{};if(b.nodeType)b=a.data(b,"tmplPlugin")||a.data(b,"tmplPlugin",o(b.innerHTML));return typeof c==="string"?(a.template[c]=b):b}return c?typeof c!=="string"?a.template(null,c):a.template[c]||a.template(null,q.test(c)?c:a(c)):null},encode:function(a){return(""+a).split("<").join("&lt;").split(">").join("&gt;").split('"').join("&#34;").split("'").join("&#39;")}});a.extend(a.tmplPlugin,{tag:{tmplPlugin:{_default:{$2:"null"},open:"if($notnull_1){__=__.concat($item.nest($1,$2));}"},wrap:{_default:{$2:"null"},open:"$item.calls(__,$1,$2);__=[];",close:"call=$item.calls();__=call._.concat($item.wrap(call,__));"},each:{_default:{$2:"$index, $value"},open:"if($notnull_1){$.each($1a,function($2){with(this){",close:"}});}"},"if":{open:"if(($notnull_1) && $1a){",close:"}"},"else":{_default:{$1:"true"},open:"}else if(($notnull_1) && $1a){"},html:{open:"if($notnull_1){__.push($1a);}"},"=":{_default:{$1:"$data"},open:"if($notnull_1){__.push($.encode($1a));}"},"!":{open:""}},complete:function(){b={}},afterManip:function(f,b,d){var e=b.nodeType===11?a.makeArray(b.childNodes):b.nodeType===1?[b]:[];d.call(f,b);m(e);c++}});function j(e,g,f){var b,c=f?a.map(f,function(a){return typeof a==="string"?e.key?a.replace(/(<\w+)(?=[\s>])(?![^>]*_tmplitem)([^>]*)/g,"$1 "+d+'="'+e.key+'" $2'):a:j(a,e,a._ctnt)}):e;if(g)return c;c=c.join("");c.replace(/^\s*([^<\s][^<]*)?(<[\w\W]+>)([^>]*[^>\s])?\s*$/,function(f,c,e,d){b=a(e).get();m(b);if(c)b=k(c).concat(b);if(d)b=b.concat(k(d))});return b?b:k(c)}function k(c){var b=document.createElement("div");b.innerHTML=c;return a.makeArray(b.childNodes)}function o(b){return new Function("jQuery","$item","var $=jQuery,call,__=[],$data=$item.data;with($data){__.push('"+a.trim(b).replace(/([\\'])/g,"\\$1").replace(/[\r\t\n]/g," ").replace(/\$\{([^\}]*)\}/g,"{{= $1}}").replace(/\{\{(\/?)(\w+|.)(?:\(((?:[^\}]|\}(?!\}))*?)?\))?(?:\s+(.*?)?)?(\(((?:[^\}]|\}(?!\}))*?)\))?\s*\}\}/g,function(m,l,k,g,b,c,d){var j=a.tmplPlugin.tag[k],i,e,f;if(!j)throw"Unknown template tag: "+k;i=j._default||[];if(c&&!/\w$/.test(b)){b+=c;c=""}if(b){b=h(b);d=d?","+h(d)+")":c?")":"";e=c?b.indexOf(".")>-1?b+h(c):"("+b+").call($item"+d:b;f=c?e:"(typeof("+b+")==='function'?("+b+").call($item):("+b+"))"}else f=e=i.$1||"null";g=h(g);return"');"+j[l?"close":"open"].split("$notnull_1").join(b?"typeof("+b+")!=='undefined' && ("+b+")!=null":"true").split("$1a").join(f).split("$1").join(e).split("$2").join(g||i.$2||"")+"__.push('"})+"');}return __;")}function n(c,b){c._wrap=j(c,true,a.isArray(b)?b:[q.test(b)?b:a(b).html()]).join("")}function h(a){return a?a.replace(/\\'/g,"'").replace(/\\\\/g,"\\"):null}function s(b){var a=document.createElement("div");a.appendChild(b.cloneNode(true));return a.innerHTML}function m(o){var n="_"+c,k,j,l={},e,p,h;for(e=0,p=o.length;e<p;e++){if((k=o[e]).nodeType!==1)continue;j=k.getElementsByTagName("*");for(h=j.length-1;h>=0;h--)m(j[h]);m(k)}function m(j){var p,h=j,k,e,m;if(m=j.getAttribute(d)){while(h.parentNode&&(h=h.parentNode).nodeType===1&&!(p=h.getAttribute(d)));if(p!==m){h=h.parentNode?h.nodeType===11?0:h.getAttribute(d)||0:0;if(!(e=b[m])){e=f[m];e=g(e,b[h]||f[h]);e.key=++i;b[i]=e}c&&o(m)}j.removeAttribute(d)}else if(c&&(e=a.data(j,"tmplItem"))){o(e.key);b[e.key]=e;h=a.data(j.parentNode,"tmplItem");h=h?h.key:0}if(e){k=e;while(k&&k.key!=h){k.nodes.push(j);k=k.parent}delete e._ctnt;delete e._wrap;a.data(j,"tmplItem",e)}function o(a){a=a+n;e=l[a]=l[a]||g(e,b[e.parent.key+n]||e.parent)}}}function u(a,d,c,b){if(!a)return l.pop();l.push({_:a,tmplPlugin:d,item:this,data:c,options:b})}function w(d,c,b){return a.tmplPlugin(a.template(d),c,b,this)}function x(b,d){var c=b.options||{};c.wrapped=d;return a.tmplPlugin(a.template(b.tmplPlugin),b.data,c,b.item)}function v(d,c){var b=this._wrap;return a.map(a(a.isArray(b)?b.join(""):b).filter(d||"*"),function(a){return c?a.innerText||a.textContent:a.outerHTML||s(a)})}function t(){var b=this.nodes;a.tmplPlugin(null,null,null,this).insertBefore(b[0]);a(b).remove()}})(jQuery);

/*
 * jQuery TableSorter plugin
 * http://autobahn.tablesorter.com/jquery.tablesorter.min.js
 */

(function($){$.extend({tablesorter:new
function(){var parsers=[],widgets=[];this.defaults={cssHeader:"header",cssAsc:"headerSortUp",cssDesc:"headerSortDown",cssChildRow:"expand-child",sortInitialOrder:"asc",sortMultiSortKey:"shiftKey",sortForce:null,sortAppend:null,sortLocaleCompare:true,textExtraction:"simple",parsers:{},widgets:[],widgetZebra:{css:["even","odd"]},headers:{},widthFixed:false,cancelSelection:true,sortList:[],headerList:[],dateFormat:"us",decimal:'/\.|\,/g',onRenderHeader:null,selectorHeaders:'thead th',debug:false};function benchmark(s,d){log(s+","+(new Date().getTime()-d.getTime())+"ms");}this.benchmark=benchmark;function log(s){if(typeof console!="undefined"&&typeof console.debug!="undefined"){console.log(s);}else{alert(s);}}function buildParserCache(table,$headers){if(table.config.debug){var parsersDebug="";}if(table.tBodies.length==0)return;var rows=table.tBodies[0].rows;if(rows[0]){var list=[],cells=rows[0].cells,l=cells.length;for(var i=0;i<l;i++){var p=false;if($.metadata&&($($headers[i]).metadata()&&$($headers[i]).metadata().sorter)){p=getParserById($($headers[i]).metadata().sorter);}else if((table.config.headers[i]&&table.config.headers[i].sorter)){p=getParserById(table.config.headers[i].sorter);}if(!p){p=detectParserForColumn(table,rows,-1,i);}if(table.config.debug){parsersDebug+="column:"+i+" parser:"+p.id+"\n";}list.push(p);}}if(table.config.debug){log(parsersDebug);}return list;};function detectParserForColumn(table,rows,rowIndex,cellIndex){var l=parsers.length,node=false,nodeValue=false,keepLooking=true;while(nodeValue==''&&keepLooking){rowIndex++;if(rows[rowIndex]){node=getNodeFromRowAndCellIndex(rows,rowIndex,cellIndex);nodeValue=trimAndGetNodeText(table.config,node);if(table.config.debug){log('Checking if value was empty on row:'+rowIndex);}}else{keepLooking=false;}}for(var i=1;i<l;i++){if(parsers[i].is(nodeValue,table,node)){return parsers[i];}}return parsers[0];}function getNodeFromRowAndCellIndex(rows,rowIndex,cellIndex){return rows[rowIndex].cells[cellIndex];}function trimAndGetNodeText(config,node){return $.trim(getElementText(config,node));}function getParserById(name){var l=parsers.length;for(var i=0;i<l;i++){if(parsers[i].id.toLowerCase()==name.toLowerCase()){return parsers[i];}}return false;}function buildCache(table){if(table.config.debug){var cacheTime=new Date();}var totalRows=(table.tBodies[0]&&table.tBodies[0].rows.length)||0,totalCells=(table.tBodies[0].rows[0]&&table.tBodies[0].rows[0].cells.length)||0,parsers=table.config.parsers,cache={row:[],normalized:[]};for(var i=0;i<totalRows;++i){var c=$(table.tBodies[0].rows[i]),cols=[];if(c.hasClass(table.config.cssChildRow)){cache.row[cache.row.length-1]=cache.row[cache.row.length-1].add(c);continue;}cache.row.push(c);for(var j=0;j<totalCells;++j){cols.push(parsers[j].format(getElementText(table.config,c[0].cells[j]),table,c[0].cells[j]));}cols.push(cache.normalized.length);cache.normalized.push(cols);cols=null;};if(table.config.debug){benchmark("Building cache for "+totalRows+" rows:",cacheTime);}return cache;};function getElementText(config,node){var text="";if(!node)return"";if(!config.supportsTextContent)config.supportsTextContent=node.textContent||false;if(config.textExtraction=="simple"){if(config.supportsTextContent){text=node.textContent;}else{if(node.childNodes[0]&&node.childNodes[0].hasChildNodes()){text=node.childNodes[0].innerHTML;}else{text=node.innerHTML;}}}else{if(typeof(config.textExtraction)=="function"){text=config.textExtraction(node);}else{text=$(node).text();}}return text;}function appendToTable(table,cache){if(table.config.debug){var appendTime=new Date()}var c=cache,r=c.row,n=c.normalized,totalRows=n.length,checkCell=(n[0].length-1),tableBody=$(table.tBodies[0]),rows=[];for(var i=0;i<totalRows;i++){var pos=n[i][checkCell];rows.push(r[pos]);if(!table.config.appender){var l=r[pos].length;for(var j=0;j<l;j++){tableBody[0].appendChild(r[pos][j]);}}}if(table.config.appender){table.config.appender(table,rows);}rows=null;if(table.config.debug){benchmark("Rebuilt table:",appendTime);}applyWidget(table);setTimeout(function(){$(table).trigger("sortEnd");},0);};function buildHeaders(table){if(table.config.debug){var time=new Date();}var meta=($.metadata)?true:false;var header_index=computeTableHeaderCellIndexes(table);$tableHeaders=$(table.config.selectorHeaders,table).each(function(index){this.column=header_index[this.parentNode.rowIndex+"-"+this.cellIndex];this.order=formatSortingOrder(table.config.sortInitialOrder);this.count=this.order;if(checkHeaderMetadata(this)||checkHeaderOptions(table,index))this.sortDisabled=true;if(checkHeaderOptionsSortingLocked(table,index))this.order=this.lockedOrder=checkHeaderOptionsSortingLocked(table,index);if(!this.sortDisabled){var $th=$(this).addClass(table.config.cssHeader);if(table.config.onRenderHeader)table.config.onRenderHeader.apply($th);}table.config.headerList[index]=this;});if(table.config.debug){benchmark("Built headers:",time);log($tableHeaders);}return $tableHeaders;};function computeTableHeaderCellIndexes(t){var matrix=[];var lookup={};var thead=t.getElementsByTagName('THEAD')[0];var trs=thead.getElementsByTagName('TR');for(var i=0;i<trs.length;i++){var cells=trs[i].cells;for(var j=0;j<cells.length;j++){var c=cells[j];var rowIndex=c.parentNode.rowIndex;var cellId=rowIndex+"-"+c.cellIndex;var rowSpan=c.rowSpan||1;var colSpan=c.colSpan||1
var firstAvailCol;if(typeof(matrix[rowIndex])=="undefined"){matrix[rowIndex]=[];}for(var k=0;k<matrix[rowIndex].length+1;k++){if(typeof(matrix[rowIndex][k])=="undefined"){firstAvailCol=k;break;}}lookup[cellId]=firstAvailCol;for(var k=rowIndex;k<rowIndex+rowSpan;k++){if(typeof(matrix[k])=="undefined"){matrix[k]=[];}var matrixrow=matrix[k];for(var l=firstAvailCol;l<firstAvailCol+colSpan;l++){matrixrow[l]="x";}}}}return lookup;}function checkCellColSpan(table,rows,row){var arr=[],r=table.tHead.rows,c=r[row].cells;for(var i=0;i<c.length;i++){var cell=c[i];if(cell.colSpan>1){arr=arr.concat(checkCellColSpan(table,headerArr,row++));}else{if(table.tHead.length==1||(cell.rowSpan>1||!r[row+1])){arr.push(cell);}}}return arr;};function checkHeaderMetadata(cell){if(($.metadata)&&($(cell).metadata().sorter===false)){return true;};return false;}function checkHeaderOptions(table,i){if((table.config.headers[i])&&(table.config.headers[i].sorter===false)){return true;};return false;}function checkHeaderOptionsSortingLocked(table,i){if((table.config.headers[i])&&(table.config.headers[i].lockedOrder))return table.config.headers[i].lockedOrder;return false;}function applyWidget(table){var c=table.config.widgets;var l=c.length;for(var i=0;i<l;i++){getWidgetById(c[i]).format(table);}}function getWidgetById(name){var l=widgets.length;for(var i=0;i<l;i++){if(widgets[i].id.toLowerCase()==name.toLowerCase()){return widgets[i];}}};function formatSortingOrder(v){if(typeof(v)!="Number"){return(v.toLowerCase()=="desc")?1:0;}else{return(v==1)?1:0;}}function isValueInArray(v,a){var l=a.length;for(var i=0;i<l;i++){if(a[i][0]==v){return true;}}return false;}function setHeadersCss(table,$headers,list,css){$headers.removeClass(css[0]).removeClass(css[1]);var h=[];$headers.each(function(offset){if(!this.sortDisabled){h[this.column]=$(this);}});var l=list.length;for(var i=0;i<l;i++){h[list[i][0]].addClass(css[list[i][1]]);}}function fixColumnWidth(table,$headers){var c=table.config;if(c.widthFixed){var colgroup=$('<colgroup>');$("tr:first td",table.tBodies[0]).each(function(){colgroup.append($('<col>').css('width',$(this).width()));});$(table).prepend(colgroup);};}function updateHeaderSortCount(table,sortList){var c=table.config,l=sortList.length;for(var i=0;i<l;i++){var s=sortList[i],o=c.headerList[s[0]];o.count=s[1];o.count++;}}function multisort(table,sortList,cache){if(table.config.debug){var sortTime=new Date();}var dynamicExp="var sortWrapper = function(a,b) {",l=sortList.length;for(var i=0;i<l;i++){var c=sortList[i][0];var order=sortList[i][1];var s=(table.config.parsers[c].type=="text")?((order==0)?makeSortFunction("text","asc",c):makeSortFunction("text","desc",c)):((order==0)?makeSortFunction("numeric","asc",c):makeSortFunction("numeric","desc",c));var e="e"+i;dynamicExp+="var "+e+" = "+s;dynamicExp+="if("+e+") { return "+e+"; } ";dynamicExp+="else { ";}var orgOrderCol=cache.normalized[0].length-1;dynamicExp+="return a["+orgOrderCol+"]-b["+orgOrderCol+"];";for(var i=0;i<l;i++){dynamicExp+="}; ";}dynamicExp+="return 0; ";dynamicExp+="}; ";if(table.config.debug){benchmark("Evaling expression:"+dynamicExp,new Date());}eval(dynamicExp);cache.normalized.sort(sortWrapper);if(table.config.debug){benchmark("Sorting on "+sortList.toString()+" and dir "+order+" time:",sortTime);}return cache;};function makeSortFunction(type,direction,index){var a="a["+index+"]",b="b["+index+"]";if(type=='text'&&direction=='asc'){return"("+a+" == "+b+" ? 0 : ("+a+" === null ? Number.POSITIVE_INFINITY : ("+b+" === null ? Number.NEGATIVE_INFINITY : ("+a+" < "+b+") ? -1 : 1 )));";}else if(type=='text'&&direction=='desc'){return"("+a+" == "+b+" ? 0 : ("+a+" === null ? Number.POSITIVE_INFINITY : ("+b+" === null ? Number.NEGATIVE_INFINITY : ("+b+" < "+a+") ? -1 : 1 )));";}else if(type=='numeric'&&direction=='asc'){return"("+a+" === null && "+b+" === null) ? 0 :("+a+" === null ? Number.POSITIVE_INFINITY : ("+b+" === null ? Number.NEGATIVE_INFINITY : "+a+" - "+b+"));";}else if(type=='numeric'&&direction=='desc'){return"("+a+" === null && "+b+" === null) ? 0 :("+a+" === null ? Number.POSITIVE_INFINITY : ("+b+" === null ? Number.NEGATIVE_INFINITY : "+b+" - "+a+"));";}};function makeSortText(i){return"((a["+i+"] < b["+i+"]) ? -1 : ((a["+i+"] > b["+i+"]) ? 1 : 0));";};function makeSortTextDesc(i){return"((b["+i+"] < a["+i+"]) ? -1 : ((b["+i+"] > a["+i+"]) ? 1 : 0));";};function makeSortNumeric(i){return"a["+i+"]-b["+i+"];";};function makeSortNumericDesc(i){return"b["+i+"]-a["+i+"];";};function sortText(a,b){if(table.config.sortLocaleCompare)return a.localeCompare(b);return((a<b)?-1:((a>b)?1:0));};function sortTextDesc(a,b){if(table.config.sortLocaleCompare)return b.localeCompare(a);return((b<a)?-1:((b>a)?1:0));};function sortNumeric(a,b){return a-b;};function sortNumericDesc(a,b){return b-a;};function getCachedSortType(parsers,i){return parsers[i].type;};this.construct=function(settings){return this.each(function(){if(!this.tHead||!this.tBodies)return;var $this,$document,$headers,cache,config,shiftDown=0,sortOrder;this.config={};config=$.extend(this.config,$.tablesorter.defaults,settings);$this=$(this);$.data(this,"tablesorter",config);$headers=buildHeaders(this);this.config.parsers=buildParserCache(this,$headers);cache=buildCache(this);var sortCSS=[config.cssDesc,config.cssAsc];fixColumnWidth(this);$headers.click(function(e){var totalRows=($this[0].tBodies[0]&&$this[0].tBodies[0].rows.length)||0;if(!this.sortDisabled&&totalRows>0){$this.trigger("sortStart");var $cell=$(this);var i=this.column;this.order=this.count++%2;if(this.lockedOrder)this.order=this.lockedOrder;if(!e[config.sortMultiSortKey]){config.sortList=[];if(config.sortForce!=null){var a=config.sortForce;for(var j=0;j<a.length;j++){if(a[j][0]!=i){config.sortList.push(a[j]);}}}config.sortList.push([i,this.order]);}else{if(isValueInArray(i,config.sortList)){for(var j=0;j<config.sortList.length;j++){var s=config.sortList[j],o=config.headerList[s[0]];if(s[0]==i){o.count=s[1];o.count++;s[1]=o.count%2;}}}else{config.sortList.push([i,this.order]);}};setTimeout(function(){setHeadersCss($this[0],$headers,config.sortList,sortCSS);appendToTable($this[0],multisort($this[0],config.sortList,cache));},1);return false;}}).mousedown(function(){if(config.cancelSelection){this.onselectstart=function(){return false};return false;}});$this.bind("update",function(){var me=this;setTimeout(function(){me.config.parsers=buildParserCache(me,$headers);cache=buildCache(me);},1);}).bind("updateCell",function(e,cell){var config=this.config;var pos=[(cell.parentNode.rowIndex-1),cell.cellIndex];cache.normalized[pos[0]][pos[1]]=config.parsers[pos[1]].format(getElementText(config,cell),cell);}).bind("sorton",function(e,list){$(this).trigger("sortStart");config.sortList=list;var sortList=config.sortList;updateHeaderSortCount(this,sortList);setHeadersCss(this,$headers,sortList,sortCSS);appendToTable(this,multisort(this,sortList,cache));}).bind("appendCache",function(){appendToTable(this,cache);}).bind("applyWidgetId",function(e,id){getWidgetById(id).format(this);}).bind("applyWidgets",function(){applyWidget(this);});if($.metadata&&($(this).metadata()&&$(this).metadata().sortlist)){config.sortList=$(this).metadata().sortlist;}if(config.sortList.length>0){$this.trigger("sorton",[config.sortList]);}applyWidget(this);});};this.addParser=function(parser){var l=parsers.length,a=true;for(var i=0;i<l;i++){if(parsers[i].id.toLowerCase()==parser.id.toLowerCase()){a=false;}}if(a){parsers.push(parser);};};this.addWidget=function(widget){widgets.push(widget);};this.formatFloat=function(s){var i=parseFloat(s);return(isNaN(i))?0:i;};this.formatInt=function(s){var i=parseInt(s);return(isNaN(i))?0:i;};this.isDigit=function(s,config){return/^[-+]?\d*$/.test($.trim(s.replace(/[,.']/g,'')));};this.clearTableBody=function(table){if($.browser.msie){function empty(){while(this.firstChild)this.removeChild(this.firstChild);}empty.apply(table.tBodies[0]);}else{table.tBodies[0].innerHTML="";}};}});$.fn.extend({tablesorter:$.tablesorter.construct});var ts=$.tablesorter;ts.addParser({id:"text",is:function(s){return true;},format:function(s){return $.trim(s.toLocaleLowerCase());},type:"text"});ts.addParser({id:"digit",is:function(s,table){var c=table.config;return $.tablesorter.isDigit(s,c);},format:function(s){return $.tablesorter.formatFloat(s);},type:"numeric"});ts.addParser({id:"currency",is:function(s){return/^[Â£$â‚¬?.]/.test(s);},format:function(s){return $.tablesorter.formatFloat(s.replace(new RegExp(/[Â£$â‚¬]/g),""));},type:"numeric"});ts.addParser({id:"ipAddress",is:function(s){return/^\d{2,3}[\.]\d{2,3}[\.]\d{2,3}[\.]\d{2,3}$/.test(s);},format:function(s){var a=s.split("."),r="",l=a.length;for(var i=0;i<l;i++){var item=a[i];if(item.length==2){r+="0"+item;}else{r+=item;}}return $.tablesorter.formatFloat(r);},type:"numeric"});ts.addParser({id:"url",is:function(s){return/^(https?|ftp|file):\/\/$/.test(s);},format:function(s){return jQuery.trim(s.replace(new RegExp(/(https?|ftp|file):\/\//),''));},type:"text"});ts.addParser({id:"isoDate",is:function(s){return/^\d{4}[\/-]\d{1,2}[\/-]\d{1,2}$/.test(s);},format:function(s){return $.tablesorter.formatFloat((s!="")?new Date(s.replace(new RegExp(/-/g),"/")).getTime():"0");},type:"numeric"});ts.addParser({id:"percent",is:function(s){return/\%$/.test($.trim(s));},format:function(s){return $.tablesorter.formatFloat(s.replace(new RegExp(/%/g),""));},type:"numeric"});ts.addParser({id:"usLongDate",is:function(s){return s.match(new RegExp(/^[A-Za-z]{3,10}\.? [0-9]{1,2}, ([0-9]{4}|'?[0-9]{2}) (([0-2]?[0-9]:[0-5][0-9])|([0-1]?[0-9]:[0-5][0-9]\s(AM|PM)))$/));},format:function(s){return $.tablesorter.formatFloat(new Date(s).getTime());},type:"numeric"});ts.addParser({id:"shortDate",is:function(s){return/\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}/.test(s);},format:function(s,table){var c=table.config;s=s.replace(/\-/g,"/");if(c.dateFormat=="us"){s=s.replace(/(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})/,"$3/$1/$2");}else if(c.dateFormat=="uk"){s=s.replace(/(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})/,"$3/$2/$1");}else if(c.dateFormat=="dd/mm/yy"||c.dateFormat=="dd-mm-yy"){s=s.replace(/(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2})/,"$1/$2/$3");}return $.tablesorter.formatFloat(new Date(s).getTime());},type:"numeric"});ts.addParser({id:"time",is:function(s){return/^(([0-2]?[0-9]:[0-5][0-9])|([0-1]?[0-9]:[0-5][0-9]\s(am|pm)))$/.test(s);},format:function(s){return $.tablesorter.formatFloat(new Date("2000/01/01 "+s).getTime());},type:"numeric"});ts.addParser({id:"metadata",is:function(s){return false;},format:function(s,table,cell){var c=table.config,p=(!c.parserMetadataName)?'sortValue':c.parserMetadataName;return $(cell).metadata()[p];},type:"numeric"});ts.addWidget({id:"zebra",format:function(table){if(table.config.debug){var time=new Date();}var $tr,row=-1,odd;$("tr:visible",table.tBodies[0]).each(function(i){$tr=$(this);if(!$tr.hasClass(table.config.cssChildRow))row++;odd=(row%2==0);$tr.removeClass(table.config.widgetZebra.css[odd?0:1]).addClass(table.config.widgetZebra.css[odd?1:0])});if(table.config.debug){$.tablesorter.benchmark("Applying Zebra widget",time);}}});})(jQuery);

/**
 * jQuery Cookie plugin
 *
 * Copyright (c) 2010 Klaus Hartl (stilbuero.de)
 * Dual licensed under the MIT and GPL licenses:
 * http://www.opensource.org/licenses/mit-license.php
 * http://www.gnu.org/licenses/gpl.html
 *
 */
jQuery.cookiePlugin = function (key, value, options) {

    // key and at least value given, set cookie...
    if (arguments.length > 1 && String(value) !== "[object Object]") {
        options = jQuery.extend({}, options);

        if (value === null || value === undefined) {
            options.expires = -1;
        }

        if (typeof options.expires === 'number') {
            var days = options.expires, t = options.expires = new Date();
            t.setDate(t.getDate() + days);
        }

        value = String(value);

        return (document.cookie = [
            encodeURIComponent(key), '=',
            options.raw ? value : encodeURIComponent(value),
            options.expires ? '; expires=' + options.expires.toUTCString() : '', // use expires attribute, max-age is not supported by IE
            options.path ? '; path=' + options.path : '',
            options.domain ? '; domain=' + options.domain : '',
            options.secure ? '; secure' : ''
        ].join(''));
    }

    // key and possibly options given, get cookie...
    options = value || {};
    var result, decode = options.raw ? function (s) { return s; } : decodeURIComponent;
    return (result = new RegExp('(?:^|; )' + encodeURIComponent(key) + '=([^;]*)').exec(document.cookie)) ? decode(result[1]) : null;
};
