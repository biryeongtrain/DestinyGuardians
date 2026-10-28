"""Only small throwaway repositories; never a product checkout."""
import json
import zipfile
import worktree_batch as b
import reuse_worktree_batch as reuse
from test_worktree_batch import WorktreeBatchTests

class ReuseTests(WorktreeBatchTests):
    def refresh(self,features=None):
        return reuse.refresh(self.source,{'features':features or [self.feature(scope=['src/next.txt'])]},self.root/'refresh')
    def test_delta_keeps_slot_and_unchanged_inode_with_recovery(self):
        self.create()
        unchanged=(self.worker/'scripts/tool.py').stat().st_ino
        self.write(self.worker/'src/owned.txt','integrated feature')
        self.put('src/owned.txt','integrated feature')
        self.put('src/other.txt','next dirty main')
        self.put('art/new.txt','new untracked product')
        (self.source/'art/model.bbmodel').unlink()
        before=b.scan(self.source);index=(self.source/'.git/index').read_bytes()
        report=self.refresh()
        self.assertFalse(report['mainModified']);self.assertFalse(report['recreatedWorktrees'])
        self.assertEqual((self.worker/'scripts/tool.py').stat().st_ino,unchanged)
        self.assertEqual((self.worker/'src/other.txt').read_text(),'next dirty main')
        self.assertTrue((self.worker/'art/new.txt').exists());self.assertFalse((self.worker/'art/model.bbmodel').exists())
        self.assertEqual(b.inspect(self.worker)['changes'],[])
        self.assertEqual(b.scan(self.source),before);self.assertEqual((self.source/'.git/index').read_bytes(),index)
        with zipfile.ZipFile(report['recovery']) as z:self.assertEqual(z.read('0/files/src/other.txt'),b'dirty inherited other\n')
    def test_unintegrated_owned_change_blocks_before_any_write(self):
        self.create();self.put('src/other.txt','next main')
        self.write(self.worker/'src/owned.txt','not integrated')
        before=b.scan(self.worker)
        with self.assertRaisesRegex(b.BatchError,'Unintegrated'):self.refresh()
        self.assertEqual(b.scan(self.worker),before);self.assertFalse((self.root/'refresh').exists())
    def test_out_of_scope_drift_blocks_even_if_main_has_same_bytes(self):
        self.create();self.put('src/other.txt','same');self.write(self.worker/'src/other.txt','same')
        with self.assertRaisesRegex(b.BatchError,'out-of-scope'):self.refresh()
        self.assertFalse((self.root/'refresh').exists())
    def test_new_local_main_head_advances_only_detached_slot(self):
        self.create();self.put('src/next.txt','new committed file')
        self.run_git('add','src/next.txt')
        self.run_git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','-c','commit.gpgsign=false','commit','-qm','fixture next HEAD')
        head=self.run_git('rev-parse','HEAD').strip();index=(self.source/'.git/index').read_bytes()
        self.refresh();self.assertEqual(b.git(self.worker,'rev-parse','HEAD'),head)
        self.assertEqual(b.git(self.worker,'rev-parse','--symbolic-full-name','HEAD'),'HEAD')
        self.assertEqual((self.source/'.git/index').read_bytes(),index)
    def test_dependency_delta_stays_private(self):
        self.create();self.write(self.gcb/'src/input.txt','new dependency')
        self.refresh()
        dest=self.worker/'libs/gcb-server/src/input.txt'
        self.assertEqual(dest.read_text(),'new dependency')
        self.assertNotEqual(dest.stat().st_ino,(self.gcb/'src/input.txt').stat().st_ino)
    def test_later_slot_conflict_blocks_first_slot(self):
        second=self.root/'second';features=[self.feature(),self.feature('second',second,['src/second.txt'])]
        self.create(features);self.put('src/other.txt','new main')
        self.write(second/'src/second.txt','unintegrated')
        before=b.scan(self.worker)
        with self.assertRaisesRegex(b.BatchError,'Unintegrated'):self.refresh(features)
        self.assertEqual(b.scan(self.worker),before)
