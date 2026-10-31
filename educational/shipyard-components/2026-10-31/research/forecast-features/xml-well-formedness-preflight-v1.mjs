// Schema-neutral, bounded XML 1.0 well-formedness preflight.
// This module validates syntax and selected parser-risk constructs only; it
// does not bind names to any application schema or construct a data tree.
import {SaxesParser} from 'saxes';

export const XML_WELL_FORMEDNESS_PREFLIGHT_POLICY=Object.freeze({
  id:'XML_WELL_FORMEDNESS_PREFLIGHT_V1', origin:'NEW_LOCAL_VALIDATION_POLICY',
  default_max_bytes:2*1024*1024, max_allowed_bytes:4*1024*1024,
  default_max_depth:80, max_allowed_depth:80, default_max_nodes:30000, max_allowed_nodes:100000,
  defaults:Object.freeze({allowDoctype:false,allowProcessingInstructions:false,allowComments:false,allowCdata:false,
    allowXmlDeclaration:true,rejectNamespaces:false}),
  schema_binding:false, network_access:false,
});

function fail(code){const error=new Error(code);error.code=code;throw error;}
const utf8Bytes=value=>new TextEncoder().encode(value).byteLength;

/**
 * Validate bounded XML syntax without interpreting a schema.
 * Limits may be made stricter per caller but never looser than the policy
 * maxima. DTD, non-declaration PIs, comments and CDATA are denied by default.
 */
export function validateXmlWellFormedness(source,options={}){
  if(typeof source!=='string')fail('xml_input_must_be_string');
  const opts={...XML_WELL_FORMEDNESS_PREFLIGHT_POLICY.defaults,...options};
  const maxBytes=Number(opts.maxBytes??XML_WELL_FORMEDNESS_PREFLIGHT_POLICY.default_max_bytes);
  const maxDepth=Number(opts.maxDepth??XML_WELL_FORMEDNESS_PREFLIGHT_POLICY.default_max_depth);
  const maxNodes=Number(opts.maxNodes??XML_WELL_FORMEDNESS_PREFLIGHT_POLICY.default_max_nodes);
  if(!Number.isInteger(maxBytes)||maxBytes<1||maxBytes>XML_WELL_FORMEDNESS_PREFLIGHT_POLICY.max_allowed_bytes||
    !Number.isInteger(maxDepth)||maxDepth<1||maxDepth>XML_WELL_FORMEDNESS_PREFLIGHT_POLICY.max_allowed_depth||
    !Number.isInteger(maxNodes)||maxNodes<1||maxNodes>XML_WELL_FORMEDNESS_PREFLIGHT_POLICY.max_allowed_nodes)
    fail('xml_preflight_limit_invalid');
  for(const key of ['allowDoctype','allowProcessingInstructions','allowComments','allowCdata','allowXmlDeclaration','rejectNamespaces'])
    if(typeof opts[key]!=='boolean')fail('xml_preflight_option_invalid');
  const byteLength=utf8Bytes(source);
  if(byteLength>maxBytes)fail('xml_preflight_byte_limit_exceeded');
  const parser=new SaxesParser({xmlns:true,position:false});
  let parseError=null,depth=0,maxDepthSeen=0,nodes=0,comments=0,cdataSections=0,processingInstructions=0,doctypes=0;
  parser.on('error',error=>{parseError??=error;});
  parser.on('opentag',tag=>{
    depth++;nodes++;
    maxDepthSeen=Math.max(maxDepthSeen,depth);
    if(depth>maxDepth)fail('xml_preflight_depth_limit_exceeded');
    if(nodes>maxNodes)fail('xml_preflight_node_limit_exceeded');
    if(opts.rejectNamespaces){
      const attrs=Object.values(tag.attributes??{});
      const declared=(tag.ns&&Object.keys(tag.ns).some(prefix=>prefix!==''&&prefix!=='xml'))||
        attrs.some(attribute=>attribute.name==='xmlns'||String(attribute.name??'').startsWith('xmlns:'));
      if(tag.prefix||tag.uri)fail(tag.prefix?'unsupported_xml_namespace_prefix':'unsupported_xml_namespace_declaration');
      if(declared||attrs.some(attribute=>attribute.prefix||attribute.uri))fail('unsupported_xml_namespace_declaration');
    }
  });
  parser.on('closetag',()=>{depth--;});
  parser.on('doctype',()=>{doctypes++;if(!opts.allowDoctype)fail('unsafe_xml_declaration');});
  parser.on('comment',()=>{comments++;if(!opts.allowComments)fail('unsupported_xml_comment_or_cdata');});
  parser.on('cdata',()=>{cdataSections++;if(!opts.allowCdata)fail('unsupported_xml_comment_or_cdata');});
  parser.on('processinginstruction',()=>{processingInstructions++;if(!opts.allowProcessingInstructions)fail('unsupported_xml_processing_instruction');});
  parser.on('xmldecl',declaration=>{
    if(!opts.allowXmlDeclaration||declaration.version!=='1.0')fail('unsupported_xml_processing_instruction');
  });
  try{parser.write(source).close();}
  catch(error){if(error?.code)throw error;parseError??=error;}
  if(parseError){
    const message=String(parseError.message??parseError).toLowerCase();
    if(message.includes('entity'))fail('unknown_xml_entity');
    if(message.includes('unclosed')||message.includes('unexpected close')||message.includes('unmatched closing'))fail('unbalanced_xml_document');
    fail('malformed_xml_document');
  }
  if(depth!==0)fail('unbalanced_xml_document');
  return {status:'valid',byte_length:byteLength,element_count:nodes,max_depth:maxDepthSeen,
    doctype_count:doctypes,comment_count:comments,cdata_count:cdataSections,processing_instruction_count:processingInstructions,
    schema_bound:false};
}
