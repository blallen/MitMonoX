void
num_events(char const* filename)
{
  auto* file = TFile::Open(filename);
  auto* tree = (TTree*)file->Get("events");
  cout << tree->GetEntries() << endl;
}
