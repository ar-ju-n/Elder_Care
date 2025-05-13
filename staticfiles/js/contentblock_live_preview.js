// Live preview for ContentBlock style fields in Django admin
(function() {
    function updatePreview() {
        var preview = document.getElementById('contentblock-style-preview-block');
        if (!preview) return;
        // Gather field values
        var bg = document.getElementById('id_background')?.value || '';
        var color = document.getElementById('id_text_color')?.value || '';
        var border = document.getElementById('id_border_color')?.value || '';
        var padding = document.getElementById('id_padding')?.value || '';
        var fontSize = document.getElementById('id_font_size')?.value || '';
        var fontFamily = document.getElementById('id_font_family')?.value || '';
        var boxShadow = document.getElementById('id_box_shadow')?.value || '';
        var borderRadius = document.getElementById('id_border_radius')?.value || '';
        var textAlign = document.getElementById('id_text_align')?.value || '';
        var margin = document.getElementById('id_margin')?.value || '';
        var shadowColor = document.getElementById('id_shadow_color')?.value || '';
        // Compose style
        var style = '';
        if(bg) style += `background:${bg};`;
        if(color) style += `color:${color};`;
        if(border) style += `border:2px solid ${border};`;
        if(padding) style += `padding:${padding.replace(/[^0-9]/g,'')}px;`;
        if(fontSize) style += `font-size:${fontSize.replace(/[^0-9]/g,'')}px;`;
        if(fontFamily) style += `font-family:${fontFamily};`;
        if(boxShadow) style += `box-shadow:${boxShadow};`;
        if(borderRadius) style += `border-radius:${borderRadius.replace(/[^0-9]/g,'')}px;`;
        if(textAlign) style += `text-align:${textAlign};`;
        if(margin) style += `margin:${margin.replace(/[^0-9]/g,'')}px;`;
        if(shadowColor) style += `box-shadow:0 4px 12px ${shadowColor};`;
        preview.setAttribute('style', style);
    }
    function ensurePreviewArea() {
        var content = document.getElementById('id_content');
        if (!content) return;
        var preview = document.getElementById('contentblock-style-preview');
        if (!preview) {
            preview = document.createElement('div');
            preview.id = 'contentblock-style-preview';
            preview.innerHTML = '<strong>Live Style Preview</strong><div id="contentblock-style-preview-block" style="min-height:40px;padding:8px;margin-top:6px;background:#f8f9fa;border:1px solid #ddd;">Sample content block</div>';
            content.parentNode.insertBefore(preview, content.nextSibling);
        }
    }
    function connectFields() {
        var fields = [
            'id_background','id_text_color','id_border_color','id_padding','id_font_size','id_font_family','id_box_shadow','id_border_radius','id_text_align','id_margin','id_shadow_color'
        ];
        fields.forEach(function(fid) {
            var el = document.getElementById(fid);
            if (el) el.addEventListener('input', updatePreview);
        });
    }
    document.addEventListener('DOMContentLoaded', function() {
        ensurePreviewArea();
        connectFields();
        updatePreview();
    });
})();
