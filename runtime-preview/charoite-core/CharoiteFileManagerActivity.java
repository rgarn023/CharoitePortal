package com.charoitegames.core;

import android.app.Activity;
import android.content.Intent;
import android.content.res.Configuration;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.documentfile.provider.DocumentFile;
import com.winlator.container.Container;
import com.winlator.container.ContainerManager;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Charoite-owned file manager: existing Wine C drives plus SAF-selected
 * external / former Winlator exports. Cross-app private data is never read.
 * Browser is read-only. Import/export copy without replacing originals.
 */
public final class CharoiteFileManagerActivity extends AppCompatActivity {
    private static final int LEGACY=701, FILE_OUT=702, FOLDER_OUT=703, FILE_IN=704, FOLDER_IN=705;
    private static final int PAGE=80, MAX_DEPTH=50, MAX_ITEMS=20000;
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private File drive, directory, selectedFile;
    private DocumentFile externalDir, selectedDoc;
    private final ArrayList<DocumentFile> parents=new ArrayList<>();
    private boolean external, busy;
    private int count=PAGE, currentId, fg, bg, panel, dim;
    private LinearLayout entries, actions;
    private TextView path, status, heading;
    private static final class Item {
        final File file;final DocumentFile doc;final String name;final boolean folder;final long size;
        Item(File f){file=f;doc=null;name=f.getName();folder=f.isDirectory();size=f.length();}
        Item(DocumentFile d){file=null;doc=d;name=d.getName();folder=d.isDirectory();size=d.length();}
    }
    @Override public void onCreate(Bundle b){
        super.onCreate(b);if(b!=null)currentId=b.getInt("manager_container",0);
        buildUi();initial();
    }
    @Override protected void onSaveInstanceState(Bundle b){b.putInt("manager_container",currentId);super.onSaveInstanceState(b);}
    @Override protected void onDestroy(){worker.shutdown();super.onDestroy();}
    private int dp(int n){return Math.round(getResources().getDisplayMetrics().density*n);}
    private TextView label(String value,int size,int color){
        TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(color);
        t.setPadding(dp(4),dp(6),dp(4),dp(6));return t;
    }
    private Button action(String value,Runnable callback){
        Button b=new Button(this);b.setAllCaps(false);b.setText(value);b.setTextColor(fg);
        b.setTextSize(14);b.setBackgroundTintList(null);b.setBackgroundColor(panel);
        b.setMinHeight(dp(48));b.setGravity(Gravity.CENTER_VERTICAL|Gravity.START);
        b.setOnClickListener(v->callback.run());return b;
    }
    private void add(String value,Runnable callback){
        actions.addView(action(value,callback),new LinearLayout.LayoutParams(-1,-2));
    }
    private void buildUi(){
        boolean dark=(getResources().getConfiguration().uiMode &
                Configuration.UI_MODE_NIGHT_MASK)==Configuration.UI_MODE_NIGHT_YES;
        fg=dark?0xfffafaff:0xff1a1b23;bg=dark?0xff101116:0xfff5f6fa;
        panel=dark?0xff292936:0xffe8ebfd;dim=dark?0xffc4c2ce:0xff646477;
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(16),dp(12),dp(16),dp(12));root.setBackgroundColor(bg);
        heading=label("Charoite Windows File Manager",22,fg);root.addView(heading);
        root.addView(label("Browse existing Wine containers, games and saves; export copies to Samsung My Files.",13,dim));
        root.addView(action("Choose Charoite container",this::chooseContainer));
        root.addView(action("Browse Winlator export or backup",this::chooseLegacy));
        root.addView(label("A different app's private /data/user/0 storage is blocked by Android. Select an accessible export or backup using the folder picker.",12,dim));
        path=label("",13,fg);path.setTextIsSelectable(true);root.addView(path);
        actions=new LinearLayout(this);actions.setOrientation(LinearLayout.VERTICAL);root.addView(actions);
        ScrollView scroll=new ScrollView(this);entries=new LinearLayout(this);
        entries.setOrientation(LinearLayout.VERTICAL);scroll.addView(entries);
        root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        status=label("Choose a container to browse.",12,dim);root.addView(status);
        setContentView(root);
    }
    private void initial(){
        try{
            ContainerManager m=new ContainerManager(this);
            int id=currentId>0?currentId:CharoiteEnvironments.activeContainerId(this);
            Container c=id>0?m.getContainerById(id):null;
            if(c==null&&!m.getContainers().isEmpty())c=m.getContainers().get(0);
            if(c!=null)open(c);else status.setText("No Charoite Wine container available.");
        }catch(Exception e){error(e);}
    }
    private void chooseContainer(){
        if(busy)return;
        try{
            List<Container> all=new ContainerManager(this).getContainers();
            if(all.isEmpty()){status.setText("No existing containers.");return;}
            int active=CharoiteEnvironments.activeContainerId(this);
            String[] names=new String[all.size()];
            for(int i=0;i<all.size();i++){Container c=all.get(i);
                names[i]="Container "+c.id+(c.id==active?" · Active realm":" · Existing / possibly older");
            }
            new AlertDialog.Builder(this).setTitle("Existing Charoite containers")
              .setItems(names,(d,i)->open(all.get(i))).setNegativeButton("Cancel",null).show();
        }catch(Exception e){error(e);}
    }
    private void open(Container c){
        try{
            File root=new File(c.getRootDir(),".wine/drive_c").getCanonicalFile();
            if(!root.isDirectory()){status.setText("Container has no prepared C: drive.");return;}
            drive=root;directory=root;currentId=c.id;
            external=false;externalDir=null;parents.clear();count=PAGE;
            heading.setText("Windows C: · Container "+c.id);refresh();
        }catch(Exception e){error(e);}
    }
    private static boolean safe(File f,File root){
        if(f==null||root==null||Files.isSymbolicLink(f.toPath()))return false;
        try{return f.getCanonicalFile().toPath().startsWith(root.getCanonicalFile().toPath());}
        catch(IOException e){return false;}
    }
    private void refresh(){
        actions.removeAllViews();entries.removeAllViews();
        if(external){
            if(externalDir==null)return;
            path.setText("Selected backup: "+externalDir.getName());
            add("↑ Up one folder",this::up);
            add("Export this folder to your phone",()->exportFolder(null,externalDir));
        }else{
            if(!safe(directory,drive)||!directory.isDirectory()){
                error(new IOException("This folder is outside your Wine C: drive"));return;
            }
            String rel=drive.toURI().relativize(directory.toURI()).getPath().replace('/','\\');
            path.setText("C:\\"+rel+"\n"+directory.getAbsolutePath());
            add("↑ Up one folder",this::up);
            add("Export this folder to your phone",()->exportFolder(directory,null));
            add("Import a file here (no overwrite)",()->importSelect(false));
            add("Import a folder here (no overwrite)",()->importSelect(true));
        }
        list();
    }
    private void up(){
        if(busy)return;
        if(external){
            if(!parents.isEmpty())externalDir=parents.remove(parents.size()-1);
        }else if(directory!=null&&!directory.equals(drive)){
            File parent=directory.getParentFile();if(safe(parent,drive))directory=parent;
        }
        count=PAGE;refresh();
    }
    private void list(){
        if(busy)return;
        final File local=external?null:directory;
        final DocumentFile remote=external?externalDir:null;
        final int limit=count;
        busy=true;status.setText("Reading folder…");
        worker.execute(()->{
            try{
                ArrayList<Item> list=new ArrayList<>();
                if(local!=null){
                    File[] files=local.listFiles();
                    if(files==null)throw new IOException("Cannot list folder");
                    for(File f:files)if(safe(f,drive))list.add(new Item(f));
                }else if(remote!=null){
                    for(DocumentFile d:remote.listFiles())if(d!=null&&d.getName()!=null)
                        list.add(new Item(d));
                }
                Collections.sort(list,(a,b)->a.folder!=b.folder?(a.folder?-1:1):
                        a.name.compareToIgnoreCase(b.name));
                runOnUiThread(()->{
                    busy=false;entries.removeAllViews();
                    for(int i=0;i<Math.min(limit,list.size());i++)addItem(list.get(i));
                    if(limit<list.size())entries.addView(action("Show more ("+
                            (list.size()-limit)+" remaining)",()->{count+=PAGE;refresh();}));
                    status.setText(list.size()+" entries · Original files unchanged");
                });
            }catch(Exception e){runOnUiThread(()->{busy=false;error(e);});}
        });
    }
    private void addItem(Item item){
        Button b=action((item.folder?"📁  ":"📄  ")+item.name+
                (item.folder?"":" · "+format(item.size)),()->{
            if(item.folder){
                if(item.file!=null){if(!safe(item.file,drive))return;directory=item.file;}
                else {parents.add(externalDir);externalDir=item.doc;}
                count=PAGE;refresh();
            }else{
                new AlertDialog.Builder(this).setTitle(item.name)
                    .setMessage(format(item.size)+"\nExport saves a COPY. Original file remains untouched.")
                    .setPositiveButton("Export",(d,w)->exportFile(item.file,item.doc))
                    .setNegativeButton("Close",null).show();
            }
        });
        entries.addView(b,new LinearLayout.LayoutParams(-1,-2));
    }
    private static String format(long n){
        if(n<1024)return n+" B";if(n<1048576)return (n/1024)+" KB";
        if(n<1073741824L)return (n/1048576)+" MB";
        return String.format(Locale.ROOT,"%.2f GB",n/1073741824.0);
    }
    private void chooseLegacy(){
        if(busy)return;
        Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|
                Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        startActivityForResult(i,LEGACY);
    }
    private void exportFile(File f,DocumentFile d){
        selectedFile=f;selectedDoc=d;
        Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("application/octet-stream");
        i.putExtra(Intent.EXTRA_TITLE,f==null?d.getName():f.getName());
        startActivityForResult(i,FILE_OUT);
    }
    private void exportFolder(File f,DocumentFile d){
        selectedFile=f;selectedDoc=d;
        Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        i.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
        startActivityForResult(i,FOLDER_OUT);
    }
    private void importSelect(boolean folder){
        if(busy||external)return;
        new AlertDialog.Builder(this).setTitle("Copy into Windows C: drive?")
            .setMessage("New files are allowed, but existing filenames are never replaced. Games, saves and Wine settings are not reset.")
            .setNegativeButton("Cancel",null)
            .setPositiveButton("Choose "+(folder?"folder":"file"),(d,w)->{
                Intent i=new Intent(folder?Intent.ACTION_OPEN_DOCUMENT_TREE:
                        Intent.ACTION_OPEN_DOCUMENT);
                i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                if(!folder){i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("*/*");}
                startActivityForResult(i,folder?FOLDER_IN:FILE_IN);
            }).show();
    }
    @Override protected void onActivityResult(int request,int result,@Nullable Intent data){
        super.onActivityResult(request,result,data);
        if(result!=Activity.RESULT_OK||data==null||data.getData()==null)return;
        Uri uri=data.getData();
        if(request==LEGACY){
            try{
                getContentResolver().takePersistableUriPermission(uri,
                        Intent.FLAG_GRANT_READ_URI_PERMISSION);
                DocumentFile d=DocumentFile.fromTreeUri(this,uri);
                if(d==null||!d.isDirectory())throw new IOException("Folder not accessible");
                external=true;externalDir=d;parents.clear();count=PAGE;
                heading.setText("Older Winlator / external backup");refresh();
            }catch(Exception e){error(e);}
        }else if(request==FILE_OUT){
            File file=selectedFile;DocumentFile doc=selectedDoc;
            if(file==null&&doc==null)return;
            perform("Export file",()->{
                if(file!=null&&!safe(file,drive))throw new IOException("Invalid file");
                try(InputStream in=file!=null?new FileInputStream(file):
                        getContentResolver().openInputStream(doc.getUri());
                    OutputStream out=getContentResolver().openOutputStream(uri,"w")){
                    if(in==null||out==null)throw new IOException("Cannot open destination");
                    copy(in,out);
                }
            });
        }else if(request==FOLDER_OUT){
            File file=selectedFile;DocumentFile doc=selectedDoc;
            perform("Export folder",()->{
                DocumentFile to=DocumentFile.fromTreeUri(this,uri);
                if(to==null||!to.canWrite())throw new IOException("Destination unavailable");
                String name=file!=null?file.getName():doc.getName();
                if(to.findFile(name)!=null)throw new IOException("Destination already exists: "+name);
                DocumentFile child=to.createDirectory(name);
                if(child==null)throw new IOException("Cannot create folder");
                if(file!=null)fromLocal(file,child,0,new int[]{0});
                else fromSaf(doc,child,0,new int[]{0});
            });
        }else if(request==FILE_IN){
            File parent=directory;
            DocumentFile file=DocumentFile.fromSingleUri(this,uri);
            if(file==null||file.getName()==null){error(new IOException("File unavailable"));return;}
            perform("Import file",()->{
                if(!safe(parent,drive))throw new IOException("Invalid destination");
                toLocal(file.getUri(),newChild(parent,file.getName()));
            });
        }else if(request==FOLDER_IN){
            File parent=directory;
            DocumentFile src=DocumentFile.fromTreeUri(this,uri);
            if(src==null||src.getName()==null){error(new IOException("Folder unavailable"));return;}
            perform("Import folder",()->{
                if(!safe(parent,drive))throw new IOException("Invalid destination");
                File to=newChild(parent,src.getName());
                if(!to.mkdir())throw new IOException("Could not create destination");
                fromSafToLocal(src,to,0,new int[]{0});
            });
        }
    }
    private interface Task{void run()throws Exception;}
    private void perform(String label,Task task){
        if(busy)return;
        busy=true;status.setText(label+"…");
        worker.execute(()->{
            Exception fail=null;try{task.run();}catch(Exception e){fail=e;}
            final Exception problem=fail;
            runOnUiThread(()->{
                busy=false;
                if(problem!=null)error(problem);
                else{Toast.makeText(this,label+" complete",Toast.LENGTH_LONG).show();refresh();}
            });
        });
    }
    private static void copy(InputStream in,OutputStream out)throws IOException{
        byte[] chunk=new byte[131072];int n;
        while((n=in.read(chunk))!=-1)out.write(chunk,0,n);
        out.flush();
    }
    private static String safeName(String n)throws IOException{
        if(n==null||n.isEmpty()||n.equals(".")||n.equals("..")||
                n.contains("/")||n.contains("\\")||n.indexOf('\0')>=0)
            throw new IOException("Unsafe filename");return n;
    }
    private static File newChild(File parent,String name)throws IOException{
        File f=new File(parent,safeName(name));
        if(f.exists()||Files.isSymbolicLink(f.toPath()))
            throw new IOException("Refusing to overwrite "+name);
        return f;
    }
    private void toLocal(Uri src,File target)throws IOException{
        if(!safe(target.getParentFile(),drive))throw new IOException("Invalid folder");
        File temp=File.createTempFile(".charoite-import-",".partial",target.getParentFile());
        try{
            try(InputStream in=getContentResolver().openInputStream(src);
                OutputStream out=new FileOutputStream(temp)){
                if(in==null)throw new IOException("Cannot read source");copy(in,out);
            }
            Files.move(temp.toPath(),target.toPath());
        }finally{temp.delete();}
    }
    private static void limit(int depth,int[] counter)throws IOException{
        if(depth>MAX_DEPTH||++counter[0]>MAX_ITEMS)
            throw new IOException("Copy size or nesting limit reached");
    }
    private void fromLocal(File dir,DocumentFile target,int depth,int[] counter)throws IOException{
        if(!safe(dir,drive)||!dir.isDirectory())throw new IOException("Invalid source folder");
        File[] files=dir.listFiles();if(files==null)throw new IOException("Unreadable source folder");
        for(File f:files){
            if(!safe(f,drive))continue;limit(depth,counter);
            if(target.findFile(f.getName())!=null)throw new IOException("Refusing overwrite");
            if(f.isDirectory()){
                DocumentFile next=target.createDirectory(f.getName());
                if(next==null)throw new IOException("Cannot create folder");
                fromLocal(f,next,depth+1,counter);
            }else if(f.isFile()){
                DocumentFile next=target.createFile("application/octet-stream",f.getName());
                if(next==null)throw new IOException("Cannot create file");
                try(InputStream in=new FileInputStream(f);
                    OutputStream out=getContentResolver().openOutputStream(next.getUri(),"w")){
                    if(out==null)throw new IOException("Cannot write destination");copy(in,out);
                }
            }
        }
    }
    private void fromSaf(DocumentFile dir,DocumentFile target,int depth,int[] counter)throws IOException{
        for(DocumentFile f:dir.listFiles()){
            if(f.getName()==null)continue;limit(depth,counter);
            if(target.findFile(f.getName())!=null)throw new IOException("Refusing overwrite");
            if(f.isDirectory()){
                DocumentFile next=target.createDirectory(f.getName());
                if(next==null)throw new IOException("Cannot create folder");
                fromSaf(f,next,depth+1,counter);
            }else if(f.isFile()){
                DocumentFile next=target.createFile("application/octet-stream",f.getName());
                if(next==null)throw new IOException("Cannot create file");
                try(InputStream in=getContentResolver().openInputStream(f.getUri());
                    OutputStream out=getContentResolver().openOutputStream(next.getUri(),"w")){
                    if(in==null||out==null)throw new IOException("Cannot copy file");copy(in,out);
                }
            }
        }
    }
    private void fromSafToLocal(DocumentFile dir,File target,int depth,int[] counter)throws IOException{
        for(DocumentFile f:dir.listFiles()){
            if(f.getName()==null)continue;limit(depth,counter);
            File dst=newChild(target,f.getName());
            if(f.isDirectory()){
                if(!dst.mkdir())throw new IOException("Cannot create directory");
                fromSafToLocal(f,dst,depth+1,counter);
            }else if(f.isFile())toLocal(f.getUri(),dst);
        }
    }
    private void error(Exception e){
        status.setText(e.getMessage()==null?"File operation failed":e.getMessage());
    }
}
